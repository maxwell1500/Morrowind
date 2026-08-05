"""Test: import Morrowind NIF (with collision), export with SGB, check if collision preserved."""
import bpy
import os

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")
OUTPUT_DIR = os.path.join(PROJECT_DIR, r"converted_assets\meshes")

bpy.ops.preferences.addon_enable(module="io_scene_mw")
bpy.ops.preferences.addon_enable(module="tool_export_mesh")

# Clear
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import Morrowind NIF
nif = os.path.join(MW_MESHES_DIR, r"x\ex_nord_house_03.nif")
bpy.ops.import_scene.mw(filepath=nif)

# Set up material on all meshes (existing pattern)
mat = bpy.data.materials.new(name=r"Materials\morrowind\ex_nord_house_03.mat")
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.data.materials.clear()
        obj.data.materials.append(mat)

# Don't delete collision - we want to see if SGB preserves it

# Select all and try to export
output_nif = os.path.join(OUTPUT_DIR, "test_with_collision.nif")
bpy.ops.object.select_all(action='DESELECT')
root = None
for obj in bpy.context.scene.objects:
    if obj.type == 'EMPTY' and not obj.name.startswith('Collision'):
        root = obj
        break
print(f"Root: {root.name!r}, type={root.type}")
print(f"Children: {[c.name for c in root.children]}")

# Select all meshes and root
root.select_set(True)
bpy.context.view_layer.objects.active = root
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

# Export
try:
    bpy.ops.export_scene.custom_nif(
        filepath=output_nif,
        use_internal_geom_data=True,
        export_material=False,
        export_sf_mesh_hash_result=False,
        export_template='Auto',
    )
    print(f"Export OK: {os.path.getsize(output_nif)} bytes")
except Exception as e:
    print(f"Export FAIL: {e}")
