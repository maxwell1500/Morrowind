import csv, math
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MW_CELL_SIZE = 8192.0
DEG2RAD = math.pi / 180.0
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
        if count == 8:
            x_mw = float(row["x_mw"]); y_mw = float(row["y_mw"]); z_mw = float(row["z_mw"])
            rx = float(row["rot_x"]); ry = float(row["rot_y"]); rz = float(row["rot_z"])
            x = (x_mw - gx*MW_CELL_SIZE)*50.0
            y = (y_mw - gy*MW_CELL_SIZE)*50.0
            z = z_mw
            print("Ref #8: %s" % obj)
            print("  x_mw=%.2f y_mw=%.2f z_mw=%.2f" % (x_mw, y_mw, z_mw))
            print("  rel: x=%.2f y=%.2f z=%.2f" % (x, y, z))
            print("  rot (deg): rx=%.2f ry=%.2f rz=%.2f" % (rx, ry, rz))
            print("  rot (rad): rx=%.6f ry=%.6f rz=%.6f" % (rx*DEG2RAD, ry*DEG2RAD, rz*DEG2RAD))
            break
