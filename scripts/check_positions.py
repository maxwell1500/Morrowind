import json

# Read the ESM JSON with utf-8 encoding
with open(r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Loaded {len(data)} records")

# Find Seyda Neen cells and check for position data
seyda_cells = []
for obj in data:
    if obj.get("type") == "Cell":
        name = obj.get("name", "")
        if "seyda" in name.lower():
            seyda_cells.append(obj)

print(f"\nFound {len(seyda_cells)} Seyda Neen cells")

# Check first cell's references for position data
cell = seyda_cells[0]
print(f"\nCell: {cell['name']}")
refs = cell.get("references", [])
print(f"References: {len(refs)}")
if refs:
    ref = refs[0]
    print(f"First ref keys: {list(ref.keys())}")
    print(f"First ref: {json.dumps(ref, indent=2)[:500]}")
