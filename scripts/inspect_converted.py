import sys, os, json
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)

import NifIO

path = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif"
print(f"Inspecting: {os.path.basename(path)}")

# Read with havok readable
out = NifIO.MeshConverter.ImportNifAsJson(path, True, path + ".havok.txt")
data = json.loads(out)

print(f"Top-level keys: {list(data.keys())}")
print(f"\nChildren:")
for i, c in enumerate(data.get('children', [])):
    if isinstance(c, dict):
        print(f"  [{i}] name={c.get('name', '?')!r}")

print(f"\nGeometries: {len(data.get('geometries', []))}")
for i, g in enumerate(data.get('geometries', [])):
    if isinstance(g, dict):
        print(f"  [{i}] mat_path={g.get('mat_path', '?')!r}, keys={list(g.keys())}")

# Look for any collision references
def walk(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ('collision', 'coll', 'havok', 'bhk', 'rigid'):
                print(f"  KEY '{k}' at {path}: {type(v).__name__}")
            if isinstance(v, (dict, list)):
                walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")

walk(data)
