"""
Test pipeline: Import Morrowind NIF → Export Starfield .mesh + .nif
Run with: blender --background --python scripts/test_pipeline.py
"""
import bpy
import os
import sys
import shutil

# Paths
MW_NIF = r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes\d\ex_nord_door_01.nif"
OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets\test_pipeline"

if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

bpy.ops.preferences.addon_enable(module="io_scene_mw")
bpy.ops.preferences.addon_enable(module="tool_export_mesh")

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

print(f"Importing {MW_NIF}...")
bpy.ops.import_scene.mw(filepath=MW_NIF)
print("Import complete.")

print("Scene:")
for obj in bpy.context.scene.objects:
    print(f"  {obj.type}: {obj.name} (parent={obj.parent.name if obj.parent else 'None'})")

# Find root empty
root_empty = None
for obj in bpy.context.scene.objects:
    if obj.type == 'EMPTY' and obj.name.startswith('Ex_'):
        root_empty = obj
        break

if root_empty is None:
    print("No root empty found! Trying any EMPTY...")
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY':
            root_empty = obj
            print(f"  Using: {obj.name}")
            break

if root_empty is None:
    print("ERROR: No empty found at all")
    sys.exit(1)

# Delete everything we don't want
keep = {root_empty.name}
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and obj.name.startswith('Tri'):
        keep.add(obj.name)

to_delete = [obj for obj in bpy.context.scene.objects if obj.name not in keep]
if to_delete:
    print(f"Deleting {len(to_delete)} objects: {[o.name for o in to_delete]}")
    bpy.ops.object.select_all(action='DESELECT')
    for obj in to_delete:
        obj.select_set(True)
    bpy.ops.object.delete()

# Ensure UV maps
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and len(obj.data.uv_layers) == 0:
        obj.data.uv_layers.new(name="UVMap")

# Select root and children for export
bpy.ops.object.select_all(action='DESELECT')
root_empty.select_set(True)
bpy.context.view_layer.objects.active = root_empty
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

print("\nFinal scene:")
for obj in bpy.context.scene.objects:
    sel = " [SELECTED]" if obj.select_get() else ""
    print(f"  {obj.type}: {obj.name}{sel}")

# Export .nif
nif_output = os.path.join(OUTPUT_DIR, "ex_nord_door_01.nif")
print(f"\nExporting .nif...")
try:
    bpy.ops.export_scene.custom_nif(
        filepath=nif_output,
        use_internal_geom_data=False,
        export_material=False,
        export_sf_mesh_hash_result=False,
        export_template='None'
    )
    print(".nif export SUCCESS!")
except Exception as e:
    print(f".nif export failed: {e}")

# List output
print(f"\nOutput files:")
for root, dirs, files in os.walk(OUTPUT_DIR):
    for f in files:
        fpath = os.path.join(root, f)
        rel = os.path.relpath(fpath, OUTPUT_DIR)
        print(f"  {rel} ({os.path.getsize(fpath)} bytes)")
