import sys, os, json
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)

import NifIO

paths = [
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModel01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif",
]

for path in paths:
    print(f"\n===== {os.path.basename(path)} =====")
    try:
        out = NifIO.MeshConverter.ImportNifAsJson(path, True, path + ".havok.txt")
        data = json.loads(out)
        print(f"Top-level keys: {list(data.keys())}")
        print(f"Children: {len(data.get('children', []))}")
        for i, c in enumerate(data.get('children', [])[:15]):
            if isinstance(c, dict):
                print(f"  [{i}] name={c.get('name', '?')!r}")

        # Look for any collision/havok keys recursively
        def walk(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(s in k.lower() for s in ('collision', 'coll', 'havok', 'bhk', 'rigid', 'hkxs', 'hkx', 'hkp', 'hcl', 'behavior', 'col_obj')):
                        if isinstance(v, (dict, list)):
                            print(f"  KEY '{k}' at {path}: {type(v).__name__} len={len(v)}")
                        else:
                            print(f"  KEY '{k}' at {path}: {v!r}")
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        walk(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")

        walk(data)
    except Exception as e:
        print(f"ERROR: {e}")

    # Check havok file
    if os.path.exists(path + ".havok.txt"):
        sz = os.path.getsize(path + ".havok.txt")
        print(f"\nHavok debug file: {sz} bytes")
        if sz < 2000:
            with open(path + ".havok.txt") as f:
                print(f.read()[:1500])
