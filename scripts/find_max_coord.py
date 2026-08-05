import csv
rows = list(csv.DictReader(open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv')))
max_coord = 0
max_row = None
for r in rows:
    for k in ['x_sf', 'y_sf', 'z_sf']:
        v = abs(float(r[k]))
        if v > max_coord:
            max_coord = v
            max_row = (r, k, v)
print('Max abs coordinate:', max_coord, 'in', max_row)
# Count how many have abs > 100000
big = [r for r in rows if max(abs(float(r['x_sf'])), abs(float(r['y_sf'])), abs(float(r['z_sf']))) > 100000]
print(f'References with any coord >100000: {len(big)}')
