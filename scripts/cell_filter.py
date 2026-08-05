import csv
rows = list(csv.DictReader(open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv')))
exterior = [r for r in rows if r['cell'] == 'Seyda Neen']
cell_mw = (-2, -9)
cell_size = 8192
ox, oy = cell_mw[0]*cell_size, cell_mw[1]*cell_size
refs = []
for r in exterior:
    x = float(r['x_mw']) - ox
    y = float(r['y_mw']) - oy
    if -cell_size/2 <= x <= cell_size/2 and -cell_size/2 <= y <= cell_size/2:
        refs.append(r)
print(f'Refs in Morrowind cell (-2,-9): {len(refs)}')
for i, r in enumerate(refs[:10]):
    x = float(r['x_mw']) - ox
    y = float(r['y_mw']) - oy
    print(f'{r["object_id"]} local ({x*50:.0f}, {y*50:.0f}, {float(r["z_mw"])*50:.0f})')
