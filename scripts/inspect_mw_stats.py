"""Count meshes in a Morrowind NIF, with and without collision."""
import bpy
import os

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")

# Test multiple NIFs
test_nifs = [
    r"x\ex_nord_house_03.nif",
    r"a\ex_ashl_chapel_01.nif",
    r"f\flora_bc_tree_02.nif",
]

bpy.ops.preferences.addon_enable(module="io_scene_mw")

for nif_rel in test_nifs:
    nif = os.path.join(MW_MESHES_DIR, nif_rel)
    if not os.path.exists(nif):
        continue
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.import_scene.mw(filepath=nif)

    all_meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    coll = [o for o in all_meshes if o.parent and 'ollision' in o.parent.name]
    main = [o for o in all_meshes if not (o.parent and 'ollision' in o.parent.name)]

    print(f"\n{os.path.basename(nif)}:")
    print(f"  Total meshes: {len(all_meshes)}")
    print(f"  Main: {len(main)}, Collision: {len(coll)}")
    print(f"  Collision verts total: {sum(len(o.data.vertices) for o in coll)}")
    print(f"  Main verts total: {sum(len(o.data.vertices) for o in main)}")
