import csv
rows = list(csv.DictReader(open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv')))
exterior = [r for r in rows if r['cell'] == 'Seyda Neen']
print(f'Exterior REFRs total: {len(exterior)}')
for i, r in enumerate(exterior[:20]):
    print(f'{i}: object_id={r["object_id"]} mesh={r["mesh_converted"]} x_sf={r["x_sf"]} y_sf={r["y_sf"]} z_sf={r["z_sf"]} rot_x={r["rot_x"]} rot_y={r["rot_y"]} rot_z={r["rot_z"]}')
