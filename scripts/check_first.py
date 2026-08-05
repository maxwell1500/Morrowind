import csv
with open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv') as f:
    r = csv.DictReader(f)
    row = next(r)
    print(f"First: {row['object_id']} x_sf={row['x_sf']} y_sf={row['y_sf']}")
