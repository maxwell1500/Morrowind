import csv, math
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"
MW_CELL_SIZE = 8192.0

# Build sorted list of converted objects
converted = set()
with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["mesh_converted"].strip().lower() == "true":
            converted.add(row["object_id"].strip().lower())

sorted_objects = sorted(converted)
print("First 10 alphabetically sorted converted objects:")
for i, obj in enumerate(sorted_objects[:10]):
    print("  %d: %s" % (i, obj))

# Now find which objects the first 10 exterior refs in grid (-2,-10) use
print("\nFirst 10 exterior refs in grid (-2,-10):")
count = 0
with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["cell"].strip() != "Seyda Neen":
            continue
        x_mw = float(row["x_mw"]); y_mw = float(row["y_mw"])
        gx = int(math.floor(x_mw / MW_CELL_SIZE))
        gy = int(math.floor(y_mw / MW_CELL_SIZE))
        if (gx, gy) != (-2, -10):
            continue
        obj = row["object_id"].strip().lower()
        if obj not in converted:
            continue
        count += 1
        if count > 10:
            break
        # Find its index in sorted_objects
        idx = sorted_objects.index(obj) if obj in sorted_objects else -1
        print("  %d: %s (STAT index %d)" % (count, obj, idx))
