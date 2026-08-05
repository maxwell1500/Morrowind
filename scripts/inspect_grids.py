import csv, math
PLACEMENT_FILE = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv'
grids = {}
with open(PLACEMENT_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['cell'].strip() != 'Seyda Neen':
            continue
        x = float(row['x_mw'])
        y = float(row['y_mw'])
        # Morrowind cell size = 8192 units
        gx = int(math.floor(x / 8192))
        gy = int(math.floor(y / 8192))
        grids[(gx, gy)] = grids.get((gx, gy), 0) + 1
for k, v in sorted(grids.items()):
    print(f'grid {k}: {v} refs')
