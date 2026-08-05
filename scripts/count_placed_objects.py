import csv
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
placed = set()
with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["mesh_converted"].strip().lower() == "true":
            placed.add(row["object_id"].strip().lower())
print("Unique converted objects placed: %d" % len(placed))
