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
        obj = row["object_id"].strip().lower()
        if row.get("mesh_converted", "").strip().lower() != "true":
            continue
        count += 1
        if count == 9:
            x = (x_mw - gx*MW_CELL_SIZE)*50.0
            y = (y_mw - gy*MW_CELL_SIZE)*50.0
            z = float(row["z_mw"])
            print("Ref #9: %s" % obj)
            print("  rel: x=%.2f y=%.2f z=%.2f" % (x, y, z))
            print("  rot: rx=%.2f ry=%.2f rz=%.2f" % (float(row["rot_x"]), float(row["rot_y"]), float(row["rot_z"])))
            break
