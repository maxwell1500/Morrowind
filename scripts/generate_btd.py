"""
BTD Generator v2 - Fixed coordinate mapping.

Key insight: BTD uses 4096-unit cells with 128x128 vertices (32 units/vertex).
Morrowind uses 8192-unit cells with 9x9 vertices.

For terrain, we need to map Morrowind heightmap into BTD grid at proper scale.
The BTD cell grid is independent of the ESP cell grid.
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

# Morrowind constants
MW_CELL_SIZE = 8192
MW_VERTICES = 9

# Our coordinate system
SCALE = 100.0 / 8192.0
OFFSET_X = -1900.0
OFFSET_Y = -1169.0
Z_OFFSET = 480.0


def interpolate_9x9_to_grid(heights_9x9, height_offset, target_w, target_h):
    """Interpolate 9x9 Morrowind grid to arbitrary resolution.
    Returns list of lists of float heights (absolute, not deltas).
    """
    # First convert deltas to absolute heights
    absolute = []
    for row in heights_9x9:
        abs_row = []
        running = float(height_offset)
        for h in row:
            running += h
            abs_row.append(running)
        absolute.append(abs_row)
    
    # Bilinear interpolation to target resolution
    result = []
    for ty in range(target_h):
        row = []
        sy = ty * 8.0 / (target_h - 1) if target_h > 1 else 0
        y0 = min(int(sy), 7)
        y1 = min(y0 + 1, 8)
        fy = sy - y0
        
        for tx in range(target_w):
            sx = tx * 8.0 / (target_w - 1) if target_w > 1 else 0
            x0 = min(int(sx), 7)
            x1 = min(x0 + 1, 8)
            fx = sx - x0
            
            h = (absolute[y0][x0] * (1-fx) * (1-fy) +
                 absolute[y0][x1] * fx * (1-fy) +
                 absolute[y1][x0] * (1-fx) * fy +
                 absolute[y1][x1] * fx * fy)
            row.append(h)
        result.append(row)
    return result


def generate_btd(cells_data, output_path):
    """Generate BTD file.
    
    cells_data: list of dicts, each with:
      - cx, cy: BTD cell coordinates
      - heights: 128x128 float array (absolute world heights)
      - textures: 128x128 uint16 array (LTEX indices)
    """
    if not cells_data:
        print("No cells to write!")
        return
    
    # Get grid bounds
    cell_xs = sorted(set(c['cx'] for c in cells_data))
    cell_ys = sorted(set(c['cy'] for c in cells_data))
    n_cells_x = len(cell_xs)
    n_cells_y = len(cell_ys)
    
    # Build lookup
    cell_lookup = {}
    for c in cells_data:
        cell_lookup[(c['cx'], c['cy'])] = c
    
    res_x = n_cells_x * VERTICES_PER_CELL
    res_y = n_cells_y * VERTICES_PER_CELL
    
    # Global height range
    all_heights = []
    for c in cells_data:
        for row in c['heights']:
            all_heights.extend(row)
    
    h_min = min(all_heights)
    h_max = max(all_heights)
    if h_max == h_min:
        h_max = h_min + 1
    
    # Scale heights for Starfield (multiply by 8.0)
    world_h_min = h_min * 8.0
    world_h_max = h_max * 8.0
    
    print(f"BTD: {n_cells_x}x{n_cells_y} cells, {res_x}x{res_y} vertices")
    print(f"Height range: {world_h_min:.1f} to {world_h_max:.1f}")
    
    # Collect LTEX indices
    all_tex = set()
    for c in cells_data:
        for row in c['textures']:
            for v in row:
                if v > 0:
                    all_tex.add(v)
    
    # Generate dummy LTEX formIDs
    ltex_formids = [0xFE000B00 + idx for idx in sorted(all_tex)]
    
    with open(output_path, 'wb') as f:
        # === Header ===
        f.write(BTD_MAGIC)
        f.write(struct.pack('<I', BTD_VERSION))
        f.write(struct.pack('<f', world_h_min))
        f.write(struct.pack('<f', world_h_max))
        f.write(struct.pack('<I', res_x))
        f.write(struct.pack('<I', res_y))
        f.write(struct.pack('<i', 0))  # CellMinX (0 for Starfield)
        f.write(struct.pack('<i', 0))  # CellMinY
        f.write(struct.pack('<i', 0))  # CellMaxX
        f.write(struct.pack('<i', 0))  # CellMaxY
        f.write(struct.pack('<I', len(ltex_formids)))
        for fid in ltex_formids:
            f.write(struct.pack('<I', fid))
        
        header_size = f.tell()
        print(f"Header: {header_size} bytes")
        
        # === Per-cell metadata ===
        for cy in cell_ys:
            for cx in cell_xs:
                c = cell_lookup.get((cx, cy))
                if c:
                    # Cell height min/max
                    ch = [h for row in c['heights'] for h in row]
                    f.write(struct.pack('<ff', min(ch) * 8.0, max(ch) * 8.0))
                    
                    # Texture map (32 bytes)
                    f.write(b'\x00' * 32)
                    
                    # LOD4 height (8x8 uint16 = 128 bytes)
                    for by in range(8):
                        for bx in range(8):
                            sy = by * 16
                            sx = bx * 16
                            vals = []
                            for dy in range(16):
                                for dx in range(16):
                                    if sy+dy < 128 and sx+dx < 128:
                                        vals.append(c['heights'][sy+dy][sx+dx])
                            avg_h = sum(vals) / len(vals) if vals else 0
                            # Convert to uint16 in BTD scale
                            raw = int(((avg_h - h_min) / (h_max - h_min)) * 65535)
                            f.write(struct.pack('<H', max(0, min(65535, raw))))
                    
                    # LOD4 texture (8x8 uint16 = 128 bytes)
                    for by in range(8):
                        for bx in range(8):
                            sy = by * 16
                            sx = bx * 16
                            vals = []
                            for dy in range(16):
                                for dx in range(16):
                                    if sy+dy < 128 and sx+dx < 128:
                                        vals.append(c['textures'][sy+dy][sx+dx])
                            avg = sum(vals) // len(vals) if vals else 0
                            f.write(struct.pack('<H', avg))
                else:
                    f.write(b'\x00' * (8 + 32 + 128 + 128))
        
        # === Block offset table ===
        n_blocks = n_cells_x * n_cells_y
        block_table_pos = f.tell()
        f.write(b'\x00' * (n_blocks * 8))
        
        # === Compressed blocks ===
        zlib_data_start = f.tell()
        block_offsets = []
        
        for cy in cell_ys:
            for cx in cell_xs:
                c = cell_lookup.get((cx, cy))
                if c:
                    # Height block: 128x128 uint16
                    height_bytes = b''
                    for row in c['heights']:
                        for h in row:
                            raw = int(((h - h_min) / (h_max - h_min)) * 65535)
                            height_bytes += struct.pack('<H', max(0, min(65535, raw)))
                    
                    # Texture block: 128x128 uint16
                    tex_bytes = b''
                    for row in c['textures']:
                        for v in row:
                            tex_bytes += struct.pack('<H', v)
                    
                    combined = height_bytes + tex_bytes
                    compressed = zlib.compress(combined, 9)
                    
                    offset = f.tell() - zlib_data_start
                    block_offsets.append((offset, len(compressed)))
                    f.write(compressed)
                else:
                    block_offsets.append((f.tell() - zlib_data_start, 0))
        
        file_end = f.tell()
        
        # Fill block table
        f.seek(block_table_pos)
        for offset, size in block_offsets:
            f.write(struct.pack('<II', offset, size))
    
    print(f"BTD written: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")


def convert_mw_to_btd(mw_data, output_path):
    """Convert Morrowind heightmap to Starfield BTD.
    
    Strategy: Each Morrowind cell (8192 units) becomes terrain within the BTD grid.
    We place BTD cells to cover the entire Morrowind area.
    """
    lands = mw_data['lands']
    
    # For each Morrowind cell, compute its BTD cell position
    # BTD cells are 4096 units. Morrowind cells are 8192 units.
    # So 1 MW cell = 2 BTD cells wide.
    
    # But our SCALE factor makes MW cells 100 units in the ESP coordinate system.
    # The BTD needs to use the SAME coordinate system as the ESP objects.
    # So: MW cell (cx,cy) covers ESP world coords:
    #   x: cx*8192*SCALE + OFFSET_X to (cx+1)*8192*SCALE + OFFSET_X
    #   y: cy*8192*SCALE + OFFSET_Y to (cy+1)*8192*SCALE + OFFSET_Y
    #   = cx*100-1900 to (cx+1)*100-1900 = cx*100-1900 to cx*100-1800
    
    # In ESP coordinates, our objects span cell (-1,-1) which is:
    #   x: -4096 to 0 (file cell) or -100 to 0 (display cell)
    
    # The BTD terrain must cover the same area as our objects.
    # Objects range: x from (-8*100-1900)=-2700 to (2*100-1900)=-1700
    #                y from (-14*100-1169)=-2569 to (-4*100-1169)=-1569
    
    # BTD cells are 4096 units in the SAME coordinate system as ESP.
    # So BTD cell (0,0) covers x: 0 to 4096, y: 0 to 4096
    #    BTD cell (-1,-1) covers x: -4096 to 0, y: -4096 to 0
    
    # Our objects are at x: -2700 to -1700, y: -2569 to -1569
    # This falls within BTD cell (-1,-1) which covers -4096 to 0 in both axes.
    
    # But we need MORE than one BTD cell for proper terrain coverage.
    # The BTD grid should cover the entire area plus some margin.
    
    # Let's use a larger BTD that covers 4096*4 = 16384 units
    # centered on our object area.
    
    # Object center: x = -2200, y = -2069
    # BTD grid: 4x4 cells = 16384 units, centered at (-2200, -2069)
    # BTD origin (cell 0,0 corner): -2200 - 8192 = -10392, -2069 - 8192 = -10261
    # But BTD cells are 4096 units, so:
    # BTD covers: x from -10392 to -10392+16384 = 5992
    #             y from -10261 to -10261+16384 = 6123
    
    # Actually, let's be smarter. The BTD cell coordinates map to world as:
    # cell_x * 4096 to (cell_x+1) * 4096
    # We need to find which BTD cells overlap our object area.
    
    # Object area in ESP coords:
    obj_x_min = -8 * 100 + OFFSET_X  # -2700
    obj_x_max = 2 * 100 + OFFSET_X   # -1700
    obj_y_min = -14 * 100 + OFFSET_Y # -2569
    obj_y_max = -4 * 100 + OFFSET_Y  # -1569
    
    # Add margin (2 BTD cells = 8192 units on each side)
    margin = 8192
    btd_x_min = int(math.floor((obj_x_min - margin) / CELL_SIZE))
    btd_x_max = int(math.floor((obj_x_max + margin) / CELL_SIZE))
    btd_y_min = int(math.floor((obj_y_min - margin) / CELL_SIZE))
    btd_y_max = int(math.floor((obj_y_max + margin) / CELL_SIZE))
    
    print(f"Object area: ({obj_x_min:.0f},{obj_y_min:.0f}) to ({obj_x_max:.0f},{obj_y_max:.0f})")
    print(f"BTD grid: ({btd_x_min},{btd_y_min}) to ({btd_x_max},{btd_y_max})")
    
    cells_data = []
    
    for btd_cy in range(btd_y_min, btd_y_max + 1):
        for btd_cx in range(btd_x_min, btd_x_max + 1):
            # BTD cell covers world coords:
            cell_x0 = btd_cx * CELL_SIZE
            cell_y0 = btd_cy * CELL_SIZE
            cell_x1 = cell_x0 + CELL_SIZE
            cell_y1 = cell_y0 + CELL_SIZE
            
            # Convert BTD cell bounds back to Morrowind cell coordinates
            # MW cell = (sf_world - OFFSET) / (8192 * SCALE) = (sf_world - OFFSET) / 100
            mw_x0 = (cell_x0 - OFFSET_X) / (MW_CELL_SIZE * SCALE)
            mw_x1 = (cell_x1 - OFFSET_X) / (MW_CELL_SIZE * SCALE)
            mw_y0 = (cell_y0 - OFFSET_Y) / (MW_CELL_SIZE * SCALE)
            mw_y1 = (cell_y1 - OFFSET_Y) / (MW_CELL_SIZE * SCALE)
            
            print(f"\nBTD cell ({btd_cx},{btd_cy}): MW range ({mw_x0:.2f},{mw_y0:.2f}) to ({mw_x1:.2f},{mw_y1:.2f})")
            
            # Find Morrowind cells that overlap this BTD cell
            mw_cx_min = int(math.floor(mw_x0))
            mw_cx_max = int(math.floor(mw_x1))
            mw_cy_min = int(math.floor(mw_y0))
            mw_cy_max = int(math.floor(mw_y1))
            
            # For each pixel in 128x128 grid, find the Morrowind height
            heights_128 = []
            textures_128 = []
            
            for vy in range(VERTICES_PER_CELL):
                h_row = []
                t_row = []
                for vx in range(VERTICES_PER_CELL):
                    # World coordinate of this vertex
                    wx = cell_x0 + vx * VERTEX_SPACING
                    wy = cell_y0 + vy * VERTEX_SPACING
                    
                    # Convert to Morrowind coordinates
                    mw_x = (wx - OFFSET_X) / (MW_CELL_SIZE * SCALE)
                    mw_y = (wy - OFFSET_Y) / (MW_CELL_SIZE * SCALE)
                    
                    # Find which Morrowind cell this is in
                    mwcx = int(math.floor(mw_x))
                    mwcy = int(math.floor(mw_y))
                    
                    # Position within the Morrowind cell (0-1)
                    frac_x = mw_x - mwcx
                    frac_y = mw_y - mwcy
                    
                    # Find the Morrowind land record
                    land = None
                    for l in lands:
                        if l['x'] == mwcx and l['y'] == mwcy:
                            land = l
                            break
                    
                    if land and 'heights' in land and land['heights']:
                        # Interpolate within the 9x9 grid
                        gx = frac_x * 8  # 0-8 within MW cell
                        gy = frac_y * 8
                        
                        x0 = min(int(gx), 7)
                        x1 = min(x0 + 1, 8)
                        y0 = min(int(gy), 7)
                        y1 = min(y0 + 1, 8)
                        fx = gx - x0
                        fy = gy - y0
                        
                        # Convert deltas to absolute
                        abs_h = []
                        for row in land['heights']:
                            abs_row = []
                            running = float(land.get('height_offset', 0))
                            for h in row:
                                running += h
                                abs_row.append(running)
                            abs_h.append(abs_row)
                        
                        h = (abs_h[y0][x0] * (1-fx) * (1-fy) +
                             abs_h[y0][x1] * fx * (1-fy) +
                             abs_h[y1][x0] * (1-fx) * fy +
                             abs_h[y1][x1] * fx * fy)
                        
                        # Texture index
                        if 'tex_indices' in land:
                            tx_idx = int(frac_x * 7)
                            ty_idx = int(frac_y * 7)
                            tex_idx = ty_idx * 8 + tx_idx
                            if tex_idx < len(land['tex_indices']):
                                t_row.append(land['tex_indices'][tex_idx])
                            else:
                                t_row.append(0)
                        else:
                            t_row.append(0)
                    else:
                        h = 0  # Default height outside Morrowind data
                        t_row.append(0)
                    
                    h_row.append(h)
                
                heights_128.append(h_row)
                textures_128.append(t_row)
            
            cells_data.append({
                'cx': btd_cx,
                'cy': btd_cy,
                'heights': heights_128,
                'textures': textures_128,
            })
    
    generate_btd(cells_data, output_path)


# === Main ===
if __name__ == '__main__':
    json_path = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\morrowind_terrain_seydaneen.json'
    output_path = r'C:\Users\max\Projects\Morrowind\Data\Terrain\Morrowind\btd_seydaneen_test.btd'
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(json_path) as f:
        mw_data = json.load(f)
    
    convert_mw_to_btd(mw_data, output_path)
