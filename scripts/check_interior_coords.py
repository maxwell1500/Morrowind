import csv, math
PLACEMENT_FILE = r"C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv"
MW_CELL_SIZE = 8192.0
for cell in ["Seyda Neen, Census and Excise Office", "Seyda Neen, Arrille's Tradehouse"]:
    xs = []
    ys = []
    zs = []
    with open(PLACEMENT_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["cell"].strip() != cell:
                continue
            xs.append(float(row["x_mw"]))
            ys.append(float(row["y_mw"]))
            zs.append(float(row["z_mw"]))
    if xs:
        print("%s: x=%.0f..%.0f y=%.0f..%.0f z=%.0f..%.0f" % (cell, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
