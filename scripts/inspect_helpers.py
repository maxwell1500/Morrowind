"""Inspect the C_ helper and Point_ nodes in a Starfield ship NIF."""
import bpy
import os
import sys
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)

import NifIO

paths = [
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModel01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif",
    r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_StorageCasing01.nif",
]

for path in paths:
    print(f"\n=== {os.path.basename(path)} ===")
    try:
        out = NifIO.MeshConverter.ImportNifAsJson(path, False, "")
        data = json.loads(out)
        # Recursively find any object names with 'C_', 'Point_', or 'Helper' prefix
        def walk(obj, path="root"):
            if isinstance(obj, dict):
                n = obj.get('name', '')
                if n and (n.startswith('C_') or n.startswith('Point_') or 'Helper' in n or 'helper' in n):
                    print(f"  HELPER at {path}: name={n!r}, type={obj.get('type_name', '?')!r}")
                # Show all children
                if 'children' in obj and obj.get('children'):
                    pass
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        walk(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")
        walk(data)
    except Exception as e:
        print(f"ERROR: {e}")
