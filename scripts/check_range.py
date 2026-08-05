import csv
with open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv') as f:
    r = csv.DictReader(f)
    for i, row in enumerate(r):
        if 58 <= i < 60:
            print(f"  [{i}] {row['object_id']}")
