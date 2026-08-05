"""Inspect the SGB JSON output for a Morrowind-converted NIF to understand its structure."""
import bpy
import os
import json
import sys
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)
import NifIO

path = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif"

# Use debug mode to get havok readable
out = NifIO.MeshConverter.ImportNifAsJson(path, True, path + ".havok.txt")
data = json.loads(out)

# Print full structure
def walk(obj, path="root", depth=0):
    if isinstance(obj, dict):
        if depth < 3:
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    if isinstance(v, dict):
                        print(f"{'  '*depth}{path}.{k} (dict): {list(v.keys())[:10]}")
                    else:
                        print(f"{'  '*depth}{path}.{k} (list[{len(v)}])")
                    if depth < 2:
                        walk(v, f"{path}.{k}", depth+1)
                else:
                    val_repr = repr(v)[:80]
                    print(f"{'  '*depth}{path}.{k} = {val_repr}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if depth < 2:
                walk(v, f"{path}[{i}]", depth+1)

# Just print top-level structure
print(f"Top-level: {list(data.keys())}")
print(f"\nTemplate RTTI: {data.get('TEMPLATE_RTTI', '?')!r}")
print(f"Name: {data.get('name', '?')!r}")
print(f"Number of children: {len(data.get('children', []))}")
print(f"Number of geometries: {len(data.get('geometries', []))}")
print(f"Skeleton mode: {data.get('skeleton_mode', '?')!r}")
print(f"Scale: {data.get('scale', '?')!r}")
print(f"SGO keep: {data.get('sgo_keep', '?')!r}")

# Show first child structure
if data.get('children'):
    c0 = data['children'][0]
    print(f"\nFirst child keys: {list(c0.keys())}")
    for k, v in c0.items():
        if isinstance(v, (dict, list)):
            print(f"  {k}: {type(v).__name__} len={len(v) if isinstance(v, (list, dict)) else 'N/A'}")
        else:
            print(f"  {k}: {v!r}")
