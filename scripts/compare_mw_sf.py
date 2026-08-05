"""Compare Morrowind and converted Starfield NIFs for the same mesh."""
import bpy
import os
import json
import sys
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
os.environ['BLENDER_USER_SCRIPTS'] = r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh"
import addon_utils
addon_utils.enable("tool_export_mesh", default_set=False, persistent=True, handle_error=None)
import NifIO

names = [
    r"x\ex_nord_house_03.nif",
    r"a\ex_ashl_chapel_01.nif",
]

MW_MESHES_DIR = r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes"
SF_MESHES_DIR = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind"

bpy.ops.preferences.addon_enable(module="io_scene_mw")

for name in names:
    base = os.path.basename(name)
    print(f"\n=== {base} ===")
    
    # Morrowind
    mw_path = os.path.join(MW_MESHES_DIR, name)
    if os.path.exists(mw_path):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.import_scene.mw(filepath=mw_path)
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        coll = [o for o in meshes if o.parent and 'ollision' in o.parent.name]
        main = [o for o in meshes if not (o.parent and 'ollision' in o.parent.name)]
        print(f"  Morrowind: {len(main)} main + {len(coll)} coll = {len(meshes)} total")
    
    # Starfield
    sf_path = os.path.join(SF_MESHES_DIR, base)
    if os.path.exists(sf_path):
        try:
            out = NifIO.MeshConverter.ImportNifAsJson(sf_path, False, "")
            data = json.loads(out)
            n_children = len(data.get('children', []))
            n_geo = len(data.get('geometries', []))
            print(f"  Starfield: {n_children} children, {n_geo} geometries")
            # Show children names
            for i, c in enumerate(data.get('children', [])):
                if isinstance(c, dict) and c.get('name', '').startswith('Object'):
                    print(f"    COLLISION LEAK: {c.get('name')!r}")
        except Exception as e:
            print(f"  Starfield: ERROR - {e}")
