import json

with open(r"C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen_inventory.json") as f:
    data = json.load(f)

print("Top-level keys:", list(data.keys()))

if "cells" in data:
    print(f"\nCells ({len(data['cells'])}):")
    for cell_name, cell_data in list(data["cells"].items())[:5]:
        print(f"  {cell_name}: {json.dumps(cell_data, indent=2)[:300]}")
