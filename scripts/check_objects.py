import json

with open(r"C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen_inventory.json") as f:
    data = json.load(f)

# Show categories
print("Categories:")
for cat, items in data.get("categories", {}).items():
    print(f"  {cat}: {len(items)} items")

# Show a few objects with their mesh references
print("\nSample objects:")
for obj in list(data.get("objects", {}).values())[:5]:
    print(f"  {json.dumps(obj, indent=2)[:300]}")
