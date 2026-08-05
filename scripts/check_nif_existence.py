import csv, os
MAPPING_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv"
MESH_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes"
count_total = 0
count_exists = 0
with open(MAPPING_FILE, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row.get("nif_converted", "").strip().lower() == "true":
            count_total += 1
            nif_name = row["object_id"].strip().lower() + ".nif"
            nif_path = os.path.join(MESH_DIR, nif_name)
            if os.path.exists(nif_path):
                count_exists += 1
print("Total converted objects: %d" % count_total)
print("NIFs that exist on disk: %d" % count_exists)
