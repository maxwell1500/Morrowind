import sys, os, json
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)

import NifIO

paths = [
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BedDouble01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_CrewChest01.nif",
]

for path in paths:
    print(f"\n===== {os.path.basename(path)} =====")
    try:
        out = NifIO.MeshConverter.ImportNifAsJson(path, True, path + ".havok.txt")
        data = json.loads(out)
        print(f"Top-level keys: {list(data.keys())}")
        for k, v in data.items():
            if k == 'children' or k == 'geometries':
                print(f"\n{k}: list of {len(v)}")
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        print(f"  [{i}] name={item.get('name', '?')!r}, type={item.get('type_name', '?')!r}, keys={list(item.keys())[:10]}")
            else:
                if isinstance(v, (dict, list)):
                    if isinstance(v, dict):
                        print(f"\n{k}: dict with keys: {list(v.keys())[:20]}")
                    else:
                        print(f"\n{k}: list of {len(v)}")
                else:
                    print(f"  {k}: {v}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Check if havok file was written
    if os.path.exists(path + ".havok.txt"):
        sz = os.path.getsize(path + ".havok.txt")
        print(f"\nHavok debug file: {sz} bytes")
        if sz < 2000:
            with open(path + ".havok.txt") as f:
                print(f.read())
