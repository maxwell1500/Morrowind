import csv
with open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        if 'ex_nord_house_01' in row.get('object_id','').lower():
            print(f"object_id={row['object_id']}")
            print(f"x_mw={row['x_mw']} y_mw={row['y_mw']} z_mw={row['z_mw']}")
            print(f"x_sf={row['x_sf']} y_sf={row['y_sf']} z_sf={row['z_sf']}")
            print(f"rot_x={row['rot_x']} rot_y={row['rot_y']} rot_z={row['rot_z']}")
            break
