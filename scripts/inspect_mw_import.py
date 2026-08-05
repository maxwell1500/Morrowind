"""Import a Morrowind NIF and inspect what's in Blender."""
import bpy
import os

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")

bpy.ops.preferences.addon_enable(module="io_scene_mw")

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import Morrowind NIF
nif = os.path.join(MW_MESHES_DIR, r"x\ex_nord_house_03.nif")
bpy.ops.import_scene.mw(filepath=nif)

# List all objects
print("=== Objects after import ===")
for obj in bpy.context.scene.objects:
    print(f"  {obj.type:6s} {obj.name!r}, parent={obj.parent.name if obj.parent else None!r}, children={len(obj.children)}")
    if obj.type == 'MESH':
        print(f"    verts={len(obj.data.vertices)}, faces={len(obj.data.polygons)}")
    if obj.children:
        for c in obj.children:
            print(f"    child: {c.type:6s} {c.name!r}, verts={len(c.data.vertices) if c.type == 'MESH' else 0}")
