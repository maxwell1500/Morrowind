"""Import a Morrowind NIF and inspect what's in the Collision empty."""
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

# Find collision
print("=== Collision hierarchy ===")
for obj in bpy.context.scene.objects:
    if obj.name.startswith('Collision') or 'ollision' in obj.name:
        print(f"COLLISION: {obj.type} {obj.name!r}, parent={obj.parent.name if obj.parent else None!r}")
        def walk(o, depth=1):
            for c in o.children:
                print(f"  {'  '*depth} child: {c.type} {c.name!r}")
                if c.type == 'MESH':
                    print(f"    verts={len(c.data.vertices)}, faces={len(c.data.polygons)}")
                    if c.data.materials:
                        for m in c.data.materials:
                            print(f"    mat: {m.name!r}")
                walk(c, depth+1)
        walk(obj)
