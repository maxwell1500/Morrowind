"""Get full SGB JSON of the ship with collision, examine its structure."""
import bpy
import os
import json
import sys
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)
import NifIO

path = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModel01.nif"

# Read as JSON
out = NifIO.MeshConverter.ImportNifAsJson(path, False, "")
data = json.loads(out)

# Save JSON to file
with open(r"C:\Users\max\Projects\Morrowind\ship_nif.json", "w") as f:
    json.dump(data, f, indent=2)
print(f"Saved {os.path.getsize(r'C:\Users\max\Projects\Morrowind\ship_nif.json')} bytes")

# Show top-level structure
print(f"\nTop-level: {list(data.keys())}")
print(f"\nTemplate RTTI: {data.get('TEMPLATE_RTTI', '?')!r}")

# Show all unique keys in the structure
def collect_keys(obj, prefix="", keys=None, depth=0):
    if keys is None:
        keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full = f"{prefix}.{k}" if prefix else k
            if full not in keys:
                keys.add(full)
            if depth < 4 and isinstance(v, (dict, list)):
                collect_keys(v, full, keys, depth+1)
    elif isinstance(obj, list) and obj and depth < 4:
        for i, v in enumerate(obj[:3]):
            collect_keys(v, f"{prefix}[{i}]", keys, depth+1)
    return keys

all_keys = collect_keys(data)
print(f"\nUnique keys ({len(all_keys)}):")
for k in sorted(all_keys):
    print(f"  {k}")
