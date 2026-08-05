import csv, math
PLACEMENT_FILE = r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv'
MW_CELL_SIZE = 8192.0
for grid in [(-2, -10), (-2, -9)]:
    print('Grid', grid)
    count = 0
    with open(PLACEMENT_FILE, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['cell'].strip() != 'Seyda Neen':
                continue
            x_mw = float(row['x_mw']); y_mw = float(row['y_mw'])
            gx = int(math.floor(x_mw / MW_CELL_SIZE))
            gy = int(math.floor(y_mw / MW_CELL_SIZE))
            if (gx, gy) != grid:
                continue
            count += 1
            if count > 10:
                break
            rx = (x_mw - gx*MW_CELL_SIZE)*50
            ry = (y_mw - gy*MW_CELL_SIZE)*50
            rz = float(row['z_mw'])*50
            print('  %s rel=(%.0f,%.0f,%.0f) rot=(%.1f,%.1f,%.1f)' % (row['object_id'], rx, ry, rz, float(row['rot_x']), float(row['rot_y']), float(row['rot_z'])))
