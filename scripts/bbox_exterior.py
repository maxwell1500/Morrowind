import csv
rows = list(csv.DictReader(open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv')))
exterior = [r for r in rows if r['cell'] == 'Seyda Neen']
xs = [float(r['x_mw']) for r in exterior]
ys = [float(r['y_mw']) for r in exterior]
zs = [float(r['z_mw']) for r in exterior]
print(f'x range: {min(xs):.1f} to {max(xs):.1f}')
print(f'y range: {min(ys):.1f} to {max(ys):.1f}')
print(f'z range: {min(zs):.1f} to {max(zs):.1f}')
print(f'Center: x={(min(xs)+max(xs))/2:.1f}, y={(min(ys)+max(ys))/2:.1f}')
print(f'Morrowind cell grid range: x={int(min(xs)//8192)}..{int(max(xs)//8192)}, y={int(min(ys)//8192)}..{int(max(ys)//8192)}')
# Count refs within 2000 units of center
cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
near = [r for r in exterior if ((float(r['x_mw'])-cx)**2 + (float(r['y_mw'])-cy)**2)**0.5 < 2000]
print(f'Within 2000 Morrowind units of center: {len(near)}')
