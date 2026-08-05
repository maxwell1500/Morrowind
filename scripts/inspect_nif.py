import sys, os, json
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils

# Enable addon
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)

import NifIO
# Read as JSON
out = NifIO.MeshConverter.ImportNifAsJson(r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes\x\ex_nord_house_03.nif", False, "")
data = json.loads(out)
# Find collision data
def walk(obj, path="root"):
    if isinstance(obj, dict):
        if 'name' in obj and 'collision' in str(obj.get('name', '')).lower():
            print(f"COLLISION NODE at {path}: {obj['name']}")
        if 'type_name' in obj and 'coll' in str(obj.get('type_name', '')).lower():
            print(f"COLLISION TYPE at {path}: {obj['type_name']}")
        for k, v in obj.items():
            walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")

walk(data)

# Also print top-level keys
print("\nTop-level keys:", list(data.keys()))
print("\nChildren names:")
if 'children' in data:
    for c in data['children']:
        if isinstance(c, dict) and 'name' in c:
            print(f"  - {c['name']} ({c.get('type_name', '?')})")
