import csv, math
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MW_CELL_SIZE = 8192.0
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
        count += 1
        if count > 10:
            break
        obj = row["object_id"].strip().lower()
        nif = "morrowind\\%s.nif" % obj
        import os
        nif_path = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes\%s" % nif
        exists = os.path.exists(nif_path)
        print("  %s -> %s exists=%s" % (obj, nif, exists))
