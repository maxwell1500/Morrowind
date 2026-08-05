"""
BTD Generator v3 — Correct Starfield format based on FrankyCLI reference.

Starfield BTD format (BTDB v6):
  Header (40 bytes):
    "BTDB" | version(6) | hMin/8 | hMax/8 | resX | resY | 0 | 0 | 0 | 0

  After header:
    LTexCount(uint32) | LTexFormIDs(uint32 * LTexCount)
    Per-cell metadata (y * countX + x order):
      heightMin/8(float) | heightMax/8(float) | texMap(32 bytes) |
      lod4Height(8x8 uint16 = 128 bytes) | lod4Tex(8x8 uint16 = 128 bytes)
    Block tables:
      LOD3: CeilDiv(CY,8)*CeilDiv(CX,8) entries of (offset,size)
      LOD2: CeilDiv(CY,4)*CeilDiv(CX,4) entries
      LOD1: CeilDiv(CY,2)*CeilDiv(CX,2) entries
      LOD0: CY*CX entries
    Compressed blocks (zlib, each decompresses to 65536 bytes):
      First 32768 bytes: 128x128 uint16 heights
      Next 32768 bytes: 128x128 uint16 textures

  Height encoding: world_h = HMin + (raw/65535) * (HMax - HMin)
  Starfield: HMin/HMax stored at 1/8 scale, cell metadata unscaled (world/8).
"""
import struct
import zlib
import json
import os
import math

BTD_MAGIC = b'BTDB'
BTD_VERSION = 6
CELL_SIZE = 4096
VERTICES_PER_CELL = 128
VERTEX_SPACING = CELL_SIZE / VERTICES_PER_CELL  # 32 units

MW_CELL_SIZE = 8192
MW_VERTICES = 9

SCALE = 100.0 / 8192.0
OFFSET_X = -1900.0
OFFSET_Y = -1169.0
Z_OFFSET = 480.0


def ceil_div(a, b):
    return (a + b - 1) // b


def build_full_heightmap(lands, cell_min_x, cell_min_y, count_x, count_y):
    """Build full-resolution height/texture maps from Morrowind land data.
    
    Returns (full_heights, full_textures) as lists of lists.
    Heights are in Starfield world coordinates.
    """
    res_x = count_x * VERTICES_PER_CELL
    res_y = count_y * VERTICES_PER_CELL
    
    # Build MW cell lookup
    mw_lookup = {}
    for land in lands:
        mw_lookup[(land['x'], land['y'])] = land
    
    full_heights = [[0.0] * res_x for _ in range(res_y)]
    full_textures = [[0] * res_x for _ in range(res_y)]
    
    for vy in range(res_y):
        for vx in range(res_x):
            # World coordinate of this vertex
            wx = vx * VERTEX_SPACING + cell_min_x * CELL_SIZE
            wy = vy * VERTEX_SPACING + cell_min_y * CELL_SIZE
            
            # Convert to Morrowind coordinates
            mw_x = (wx - OFFSET_X) / (MW_CELL_SIZE * SCALE)
            mw_y = (wy - OFFSET_Y) / (MW_CELL_SIZE * SCALE)
            
            mwcx = int(math.floor(mw_x))
            mwcy = int(math.floor(mw_y))
            
            frac_x = mw_x - mwcx
            frac_y = mw_y - mwcy
            
            land = mw_lookup.get((mwcx, mwcy))
            
            if land and 'heights' in land and land['heights']:
                # Convert deltas to absolute heights
                abs_heights = []
                for row in land['heights']:
                    abs_row = []
                    running = float(land.get('height_offset', 0))
                    for h in row:
                        running += h
                        abs_row.append(running)
                    abs_heights.append(abs_row)
                
                # Bilinear interpolation within 9x9 grid
                gx = frac_x * 8
                gy = frac_y * 8
                
                x0 = min(int(gx), 7)
                x1 = min(x0 + 1, 8)
                y0 = min(int(gy), 7)
                y1 = min(y0 + 1, 8)
                fx = gx - x0
                fy = gy - y0
                
                h = (abs_heights[y0][x0] * (1-fx) * (1-fy) +
                     abs_heights[y0][x1] * fx * (1-fy) +
                     abs_heights[y1][x0] * (1-fx) * fy +
                     abs_heights[y1][x1] * fx * fy)
                
                # Convert Morrowind height to Starfield world coordinates
                world_h = h * SCALE + Z_OFFSET
                
                # Texture index
                tx_idx = min(int(frac_x * 7), 7)
                ty_idx = min(int(frac_y * 7), 7)
                tex_idx = ty_idx * 8 + tx_idx
                if 'tex_indices' in land and tex_idx < len(land['tex_indices']):
                    tex = land['tex_indices'][tex_idx]
                else:
                    tex = 0
            else:
                world_h = Z_OFFSET  # Default height
                tex = 0
            
            full_heights[vy][vx] = world_h
            full_textures[vy][vx] = tex
    
    return full_heights, full_textures


def generate_btd(output_path, cell_min_x, cell_min_y, count_x, count_y,
                 full_heights, full_textures):
    """Write BTD file in correct Starfield format."""
    
    res_x = count_x * VERTICES_PER_CELL
    res_y = count_y * VERTICES_PER_CELL
    
    # Compute global height range
    all_h = [h for row in full_heights for h in row]
    h_min = min(all_h)
    h_max = max(all_h)
    if h_max <= h_min:
        h_max = h_min + 1.0
    
    # For Starfield header: stored at 1/8 scale
    header_h_min = h_min / 8.0
    header_h_max = h_max / 8.0
    
    print(f"BTD: {count_x}x{count_y} cells, res {res_x}x{res_y}")
    print(f"Cell range: ({cell_min_x},{cell_min_y}) to ({cell_min_x+count_x-1},{cell_min_y+count_y-1})")
    print(f"World heights: {h_min:.2f} to {h_max:.2f}")
    
    # Compute block counts per LOD
    lod_info = []
    for lod in range(4):
        cells_per_block = 1 << lod
        gw = ceil_div(count_x, cells_per_block)
        gh = ceil_div(count_y, cells_per_block)
        lod_info.append((gw, gh, gw * gh))
    
    with open(output_path, 'wb') as f:
        # === HEADER (40 bytes) ===
        f.write(BTD_MAGIC)
        f.write(struct.pack('<I', BTD_VERSION))
        f.write(struct.pack('<f', header_h_min))
        f.write(struct.pack('<f', header_h_max))
        f.write(struct.pack('<I', res_x))
        f.write(struct.pack('<I', res_y))
        f.write(struct.pack('<i', 0))  # CellMinX (0 for Starfield)
        f.write(struct.pack('<i', 0))  # CellMinY
        f.write(struct.pack('<i', 0))  # CellMaxX
        f.write(struct.pack('<i', 0))  # CellMaxY
        assert f.tell() == 40, f"Header size mismatch: {f.tell()}"
        
        # === LTEX FORMIDS (none for now) ===
        f.write(struct.pack('<I', 0))
        
        # === PER-CELL METADATA ===
        # Order: y from 0..count_y-1, x from 0..count_x-1
        for cy_idx in range(count_y):
            for cx_idx in range(count_x):
                # Cell height range from full-res data
                y0 = cy_idx * VERTICES_PER_CELL
                y1 = y0 + VERTICES_PER_CELL
                x0 = cx_idx * VERTICES_PER_CELL
                x1 = x0 + VERTICES_PER_CELL
                
                cell_h = [full_heights[y][x] for y in range(y0, y1) for x in range(x0, x1)]
                cell_h_min = min(cell_h)
                cell_h_max = max(cell_h)
                
                # Cell min/max stored UNSCALED (world / 8.0)
                f.write(struct.pack('<ff', cell_h_min / 8.0, cell_h_max / 8.0))
                
                # Texture map (32 bytes) — 4 quadrant palettes of 8 indices
                # Fill with zeros (all use texture index 0)
                f.write(b'\x00' * 32)
                
                # LOD4 height (8x8 uint16 = 128 bytes)
                for by in range(8):
                    for bx in range(8):
                        sy = min(by * 16, VERTICES_PER_CELL - 1)
                        sx = min(bx * 16, VERTICES_PER_CELL - 1)
                        h = full_heights[y0 + sy][x0 + sx]
                        raw = int(((h - h_min) / (h_max - h_min)) * 65535)
                        f.write(struct.pack('<H', max(0, min(65535, raw))))
                
                # LOD4 texture (8x8 uint16 = 128 bytes)
                for by in range(8):
                    for bx in range(8):
                        sy = min(by * 16, VERTICES_PER_CELL - 1)
                        sx = min(bx * 16, VERTICES_PER_CELL - 1)
                        t = full_textures[y0 + sy][x0 + sx]
                        f.write(struct.pack('<H', t))
        
        meta_size = f.tell()
        print(f"Metadata end: {meta_size}")
        
        # === BLOCK TABLES ===
        block_table_pos = f.tell()
        for lod in range(4):
            n = lod_info[lod][2]
            f.write(b'\x00' * (n * 8))  # placeholder
        
        block_data_start = f.tell()
        print(f"Block data starts at: {block_data_start}")
        
        # === COMPRESSED BLOCKS ===
        block_offsets = {}  # (lod, gx, gy) -> (offset, compressed_size)
        
        for lod in range(4):
            gw, gh, _ = lod_info[lod]
            cells_per_block = 1 << lod
            step = 1 << lod
            
            for gy in range(gh):
                for gx in range(gw):
                    # Build 128x128 height + texture for this block
                    height_data = bytearray(32768)  # 128*128*2
                    tex_data = bytearray(32768)      # 128*128*2
                    
                    for vy in range(VERTICES_PER_CELL):
                        for vx in range(VERTICES_PER_CELL):
                            # Map to full-resolution coordinates
                            full_vx = gx * cells_per_block * VERTICES_PER_CELL + vx * step
                            full_vy = gy * cells_per_block * VERTICES_PER_CELL + vy * step
                            
                            if full_vy < res_y and full_vx < res_x:
                                h = full_heights[full_vy][full_vx]
                                t = full_textures[full_vy][full_vx]
                            else:
                                h = Z_OFFSET
                                t = 0
                            
                            raw = int(((h - h_min) / (h_max - h_min)) * 65535)
                            raw = max(0, min(65535, raw))
                            
                            idx = (vy * VERTICES_PER_CELL + vx) * 2
                            struct.pack_into('<H', height_data, idx, raw)
                            struct.pack_into('<H', tex_data, idx, t)
                    
                    combined = bytes(height_data) + bytes(tex_data)
                    compressed = zlib.compress(combined, 6)
                    
                    offset = f.tell() - block_data_start
                    block_offsets[(lod, gx, gy)] = (offset, len(compressed))
                    f.write(compressed)
        
        file_end = f.tell()
        
        # === PATCH BLOCK TABLES ===
        f.seek(block_table_pos)
        for lod in range(4):
            gw, gh, _ = lod_info[lod]
            for gy in range(gh):
                for gx in range(gw):
                    offset, size = block_offsets.get((lod, gx, gy), (0, 0))
                    f.write(struct.pack('<II', offset, size))
        
        f.seek(file_end)
    
    fsize = os.path.getsize(output_path)
    print(f"BTD written: {output_path}")
    print(f"File size: {fsize} bytes")
    print(f"Block data: {file_end - block_data_start} bytes")


def main():
    json_path = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\morrowind_terrain_seydaneen.json'
    output_path = r'C:\Users\max\Projects\Morrowind\Data\Terrain\Morrowind\Morrowind.btd'
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(json_path) as f:
        mw_data = json.load(f)
    
    lands = mw_data['lands']
    
    # Build full height map
    # Our objects are in ESP cell (-1,-1) at world coords ~(-2200, -2069)
    # BTD cells are 4096 units. We need cells covering our area plus margin.
    
    # Object area in world coords
    obj_x_min = -8 * 100 + OFFSET_X   # -2700
    obj_x_max = 2 * 100 + OFFSET_X    # -1700
    obj_y_min = -14 * 100 + OFFSET_Y  # -2569
    obj_y_max = -4 * 100 + OFFSET_Y   # -1569
    
    margin = 8192
    cell_min_x = int(math.floor((obj_x_min - margin) / CELL_SIZE))
    cell_max_x = int(math.floor((obj_x_max + margin) / CELL_SIZE))
    cell_min_y = int(math.floor((obj_y_min - margin) / CELL_SIZE))
    cell_max_y = int(math.floor((obj_y_max + margin) / CELL_SIZE))
    
    count_x = cell_max_x - cell_min_x + 1
    count_y = cell_max_y - cell_min_y + 1
    
    print(f"Object area: ({obj_x_min:.0f},{obj_y_min:.0f}) to ({obj_x_max:.0f},{obj_y_max:.0f})")
    print(f"BTD cells: ({cell_min_x},{cell_min_y}) to ({cell_max_x},{cell_max_y})")
    print(f"Grid: {count_x}x{count_y}")
    
    # Check cell bounds match Starfield computation
    res_x = count_x * VERTICES_PER_CELL
    res_y = count_y * VERTICES_PER_CELL
    sf_cell_min_x = -(res_x >> 8)
    sf_cell_max_x = sf_cell_min_x + (res_x >> 7) - 1
    sf_cell_min_y = -(res_y >> 8)
    sf_cell_max_y = sf_cell_min_y + (res_y >> 7) - 1
    print(f"Starfield computed bounds: ({sf_cell_min_x},{sf_cell_min_y}) to ({sf_cell_max_x},{sf_cell_max_y})")
    
    if cell_min_x != sf_cell_min_x or cell_max_x != sf_cell_max_x or \
       cell_min_y != sf_cell_min_y or cell_max_y != sf_cell_max_y:
        print(f"WARNING: Cell bounds mismatch! Adjusting grid...")
        # Use Starfield-computed bounds instead
        cell_min_x = sf_cell_min_x
        cell_max_x = sf_cell_max_x
        cell_min_y = sf_cell_min_y
        cell_max_y = sf_cell_max_y
        count_x = cell_max_x - cell_min_x + 1
        count_y = cell_max_y - cell_min_y + 1
        res_x = count_x * VERTICES_PER_CELL
        res_y = count_y * VERTICES_PER_CELL
        print(f"Adjusted grid: {count_x}x{count_y}, res {res_x}x{res_y}")
    
    # Build full heightmap
    print("\nBuilding heightmap...")
    full_heights, full_textures = build_full_heightmap(
        lands, cell_min_x, cell_min_y, count_x, count_y
    )
    
    # Generate BTD
    print("\nGenerating BTD...")
    generate_btd(output_path, cell_min_x, cell_min_y, count_x, count_y,
                 full_heights, full_textures)


if __name__ == '__main__':
    main()
