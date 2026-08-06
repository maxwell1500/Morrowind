"""
BTD Generator v4 — Focused Seyda Neen terrain with edge blending.

Generates a small custom terrain patch for Seyda Neen that:
1. Uses real Morrowind LAND heights in the core village area.
2. Blends outward to a smooth edge to avoid the abrupt "floating plateau" look
   against Magnus's existing terrain.
3. Does NOT generate all of Morrowind — only the Seyda Neen neighborhood.
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

MW_CELL_SIZE = 8192.0

SCALE = 100.0 / 8192.0
OFFSET_X = 92.6
OFFSET_Y = 802.0
Z_OFFSET = 480.0

BLEND_CELLS = 2.0   # blend margin in file cells
OUTER_HEIGHT = None  # set to a fixed raw height; None = use average Morrowind edge height


def ceil_div(a, b):
    return (a + b - 1) // b


def build_land_lookup(lands):
    lookup = {}
    for land in lands:
        lookup[(land['x'], land['y'])] = land
    return lookup


def sample_morrowind_terrain(mx, my, land_lookup):
    """Sample Morrowind terrain height at Morrowind world coords (mx, my)."""
    cx = int(math.floor(mx / MW_CELL_SIZE))
    cy = int(math.floor(my / MW_CELL_SIZE))
    land = land_lookup.get((cx, cy))
    if not land or 'heights' not in land or not land['heights']:
        return None

    # Build absolute heights
    base = float(land.get('height_offset', 0.0))
    abs_heights = []
    for row in land['heights']:
        running = base
        abs_row = []
        for h in row:
            running += float(h)
            abs_row.append(running)
        abs_heights.append(abs_row)

    frac_x = (mx - cx * MW_CELL_SIZE) / MW_CELL_SIZE
    frac_y = (my - cy * MW_CELL_SIZE) / MW_CELL_SIZE
    gx = frac_x * 8.0
    gy = frac_y * 8.0
    x0 = min(int(gx), 7)
    x1 = min(x0 + 1, 8)
    y0 = min(int(gy), 7)
    y1 = min(y0 + 1, 8)
    fx = gx - x0
    fy = gy - y0

    h = (abs_heights[y0][x0] * (1 - fx) * (1 - fy) +
         abs_heights[y0][x1] * fx * (1 - fy) +
         abs_heights[y1][x0] * (1 - fx) * fy +
         abs_heights[y1][x1] * fx * fy)
    return h


def get_morrowind_bbox(land_lookup):
    """Return Morrowind world bounding box of available LAND data."""
    if not land_lookup:
        return None
    xs = [k[0] * MW_CELL_SIZE for k in land_lookup.keys()]
    ys = [k[1] * MW_CELL_SIZE for k in land_lookup.keys()]
    # Full extent of all available cells (each cell is 8192 units)
    return (min(xs), max(xs) + MW_CELL_SIZE, min(ys), max(ys) + MW_CELL_SIZE)


def build_full_heightmap(lands, cell_min_x, cell_min_y, count_x, count_y):
    """Build full-resolution height/texture maps with edge blending."""
    res_x = count_x * VERTICES_PER_CELL
    res_y = count_y * VERTICES_PER_CELL
    land_lookup = build_land_lookup(lands)

    # Morrowind data bounds in Morrowind world coords
    mw_bbox = get_morrowind_bbox(land_lookup)
    if mw_bbox:
        mw_xmin, mw_xmax, mw_ymin, mw_ymax = mw_bbox
        print(f"Morrowind data bounds (MW world): X[{mw_xmin:.0f},{mw_xmax:.0f}] Y[{mw_ymin:.0f},{mw_ymax:.0f}]")
        # Convert to Starfield world coords
        sf_xmin = mw_xmin * SCALE + OFFSET_X
        sf_xmax = mw_xmax * SCALE + OFFSET_X
        sf_ymin = mw_ymin * SCALE + OFFSET_Y
        sf_ymax = mw_ymax * SCALE + OFFSET_Y
    else:
        sf_xmin = sf_xmax = sf_ymin = sf_ymax = 0.0
    print(f"Morrowind data bounds (SF world): X[{sf_xmin:.1f},{sf_xmax:.1f}] Y[{sf_ymin:.1f},{sf_ymax:.1f}]")

    # Compute blend margin in Starfield units
    blend_margin = BLEND_CELLS * CELL_SIZE
    print(f"Blend margin: {blend_margin:.0f} SF units ({BLEND_CELLS} cells)")

    # Compute average edge height from Morrowind data
    edge_samples = []
    if mw_bbox:
        n = 32
        for i in range(n):
            t = i / (n - 1)
            # top and bottom edges
            mx = mw_xmin + t * (mw_xmax - mw_xmin)
            h = sample_morrowind_terrain(mx, mw_ymin, land_lookup)
            if h is not None:
                edge_samples.append(h)
            h = sample_morrowind_terrain(mx, mw_ymax, land_lookup)
            if h is not None:
                edge_samples.append(h)
            # left and right edges
            my = mw_ymin + t * (mw_ymax - mw_ymin)
            h = sample_morrowind_terrain(mw_xmin, my, land_lookup)
            if h is not None:
                edge_samples.append(h)
            h = sample_morrowind_terrain(mw_xmax, my, land_lookup)
            if h is not None:
                edge_samples.append(h)
    outer_h_mw = sum(edge_samples) / len(edge_samples) if edge_samples else 0.0
    if OUTER_HEIGHT is not None:
        outer_h_sf = OUTER_HEIGHT
    else:
        outer_h_sf = outer_h_mw * SCALE + Z_OFFSET
    print(f"Outer blend height: {outer_h_sf:.2f} (MW: {outer_h_mw:.1f})")

    full_heights = [[0.0] * res_x for _ in range(res_y)]
    full_textures = [[0] * res_x for _ in range(res_y)]

    for vy in range(res_y):
        for vx in range(res_x):
            wx = vx * VERTEX_SPACING + cell_min_x * CELL_SIZE
            wy = vy * VERTEX_SPACING + cell_min_y * CELL_SIZE

            # Convert to Morrowind world coords
            mx = (wx - OFFSET_X) / SCALE
            my = (wy - OFFSET_Y) / SCALE

            # Distance from Morrowind data bounding box
            dx = 0.0
            if mx < mw_xmin:
                dx = mw_xmin - mx
            elif mx > mw_xmax:
                dx = mx - mw_xmax
            dy = 0.0
            if my < mw_ymin:
                dy = mw_ymin - my
            elif my > mw_ymax:
                dy = my - mw_ymax
            dist = math.sqrt(dx * dx + dy * dy) * SCALE  # distance in SF units

            # Sample Morrowind terrain (clamped to bbox for edge extension)
            mx_clamped = max(mw_xmin, min(mx, mw_xmax))
            my_clamped = max(mw_ymin, min(my, mw_ymax))
            h_mw = sample_morrowind_terrain(mx_clamped, my_clamped, land_lookup)
            if h_mw is None:
                h_sf = outer_h_sf
            else:
                h_sf = h_mw * SCALE + Z_OFFSET

            # Blend to outer height based on distance from data bbox
            if dist <= 0.0:
                blend = 1.0
            elif dist >= blend_margin:
                blend = 0.0
            else:
                # Smoothstep-like falloff
                t = dist / blend_margin
                blend = (1.0 - t) * (1.0 - t) * (2.0 * t + 1.0)  # smoothstep

            final_h = h_sf * blend + outer_h_sf * (1.0 - blend)

            # Texture: use Morrowind tex in core, 0 outside
            tex = 0
            if h_mw is not None and dx <= 0 and dy <= 0:
                frac_x = (mx - int(math.floor(mx / MW_CELL_SIZE)) * MW_CELL_SIZE) / MW_CELL_SIZE
                frac_y = (my - int(math.floor(my / MW_CELL_SIZE)) * MW_CELL_SIZE) / MW_CELL_SIZE
                tx_idx = min(int(frac_x * 7), 7)
                ty_idx = min(int(frac_y * 7), 7)
                tex_idx = ty_idx * 8 + tx_idx
                land = land_lookup.get((int(math.floor(mx / MW_CELL_SIZE)), int(math.floor(my / MW_CELL_SIZE))))
                if land and 'tex_indices' in land and tex_idx < len(land['tex_indices']):
                    tex = land['tex_indices'][tex_idx]

            full_heights[vy][vx] = final_h
            full_textures[vy][vx] = tex

    return full_heights, full_textures


def generate_btd(output_path, cell_min_x, cell_min_y, count_x, count_y,
                 full_heights, full_textures):
    """Write BTD file in correct Starfield format."""
    res_x = count_x * VERTICES_PER_CELL
    res_y = count_y * VERTICES_PER_CELL

    all_h = [h for row in full_heights for h in row]
    h_min = min(all_h)
    h_max = max(all_h)
    if h_max <= h_min:
        h_max = h_min + 1.0

    header_h_min = h_min / 8.0
    header_h_max = h_max / 8.0

    print(f"BTD: {count_x}x{count_y} cells, res {res_x}x{res_y}")
    print(f"Cell range: ({cell_min_x},{cell_min_y}) to ({cell_min_x+count_x-1},{cell_min_y+count_y-1})")
    print(f"World heights: {h_min:.2f} to {h_max:.2f}")

    lod_info = []
    for lod in range(4):
        cells_per_block = 1 << lod
        gw = ceil_div(count_x, cells_per_block)
        gh = ceil_div(count_y, cells_per_block)
        lod_info.append((gw, gh, gw * gh))

    with open(output_path, 'wb') as f:
        f.write(BTD_MAGIC)
        f.write(struct.pack('<I', BTD_VERSION))
        f.write(struct.pack('<f', header_h_min))
        f.write(struct.pack('<f', header_h_max))
        f.write(struct.pack('<I', res_x))
        f.write(struct.pack('<I', res_y))
        f.write(struct.pack('<i', cell_min_x))
        f.write(struct.pack('<i', cell_min_y))
        f.write(struct.pack('<i', cell_min_x + count_x - 1))
        f.write(struct.pack('<i', cell_min_y + count_y - 1))
        assert f.tell() == 40, f"Header size mismatch: {f.tell()}"

        f.write(struct.pack('<I', 0))  # no LTEX formIDs

        for cy_idx in range(count_y):
            for cx_idx in range(count_x):
                y0 = cy_idx * VERTICES_PER_CELL
                x0 = cx_idx * VERTICES_PER_CELL

                cell_h = [full_heights[y][x] for y in range(y0, y0 + VERTICES_PER_CELL)
                          for x in range(x0, x0 + VERTICES_PER_CELL)]
                cell_h_min = min(cell_h)
                cell_h_max = max(cell_h)

                f.write(struct.pack('<ff', cell_h_min / 8.0, cell_h_max / 8.0))
                f.write(b'\x00' * 32)  # texture map

                for by in range(8):
                    for bx in range(8):
                        sy = min(by * 16, VERTICES_PER_CELL - 1)
                        sx = min(bx * 16, VERTICES_PER_CELL - 1)
                        h = full_heights[y0 + sy][x0 + sx]
                        raw = int(((h - h_min) / (h_max - h_min)) * 65535)
                        f.write(struct.pack('<H', max(0, min(65535, raw))))

                for by in range(8):
                    for bx in range(8):
                        sy = min(by * 16, VERTICES_PER_CELL - 1)
                        sx = min(bx * 16, VERTICES_PER_CELL - 1)
                        t = full_textures[y0 + sy][x0 + sx]
                        f.write(struct.pack('<H', t))

        meta_size = f.tell()
        print(f"Metadata end: {meta_size}")

        block_table_pos = f.tell()
        for lod in range(4):
            n = lod_info[lod][2]
            f.write(b'\x00' * (n * 8))

        block_data_start = f.tell()
        print(f"Block data starts at: {block_data_start}")

        block_offsets = {}
        for lod in range(4):
            gw, gh, _ = lod_info[lod]
            cells_per_block = 1 << lod
            step = 1 << lod

            for gy in range(gh):
                for gx in range(gw):
                    height_data = bytearray(32768)
                    tex_data = bytearray(32768)

                    for vy in range(VERTICES_PER_CELL):
                        for vx in range(VERTICES_PER_CELL):
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

    # Use a 3x3 grid centered on file cell (-1,-1) where the village sits.
    count_x = 3
    count_y = 3

    res_x = count_x * VERTICES_PER_CELL
    res_y = count_y * VERTICES_PER_CELL
    cell_min_x = -(res_x >> 8)
    cell_max_x = cell_min_x + (res_x >> 7) - 1
    cell_min_y = -(res_y >> 8)
    cell_max_y = cell_min_y + (res_y >> 7) - 1

    print(f"BTD grid: ({cell_min_x},{cell_min_y}) to ({cell_max_x},{cell_max_y}) = {count_x}x{count_y} cells")

    print("\nBuilding heightmap...")
    full_heights, full_textures = build_full_heightmap(
        lands, cell_min_x, cell_min_y, count_x, count_y
    )

    print("\nGenerating BTD...")
    generate_btd(output_path, cell_min_x, cell_min_y, count_x, count_y,
                 full_heights, full_textures)


if __name__ == '__main__':
    main()
