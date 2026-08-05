import csv, math
PLACEMENT_FILE = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv'
cell_size_mw = 8192.0
cell_size_sf = cell_size_mw * 50.0  # 409600 cm
base_map = {(-2, -10): (-200, 1000), (-2, -9): (-200, 1001)}
minx = miny = float('inf')
maxx = maxy = float('-inf')
for row in csv.DictReader(open(PLACEMENT_FILE, newline='', encoding='utf-8')):
    if row['cell'].strip() != 'Seyda Neen':
        continue
    x = float(row['x_sf'])
    y = float(row['y_sf'])
    gx = int(math.floor(float(row['x_mw']) / cell_size_mw))
    gy = int(math.floor(float(row['y_mw']) / cell_size_mw))
    sf_grid = base_map[(gx, gy)]
    rel_x = x - sf_grid[0] * cell_size_sf
    rel_y = y - sf_grid[1] * cell_size_sf
    minx = min(minx, rel_x); maxx = max(maxx, rel_x)
    miny = min(miny, rel_y); maxy = max(maxy, rel_y)
print(f'Relative coordinate ranges: x={minx:.0f}..{maxx:.0f}, y={miny:.0f}..{maxy:.0f}')
print(f'Cell size = {cell_size_sf:.0f} cm')
