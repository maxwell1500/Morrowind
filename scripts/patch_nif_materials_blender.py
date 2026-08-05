"""Import NIF in Blender, set material paths, and re-export with materials.
This uses the SGB addon's import/export which properly handles material paths."""
import bpy
import os
import sys
import json
import time

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MESHES_DIR = os.path.join(PROJECT_DIR, r"converted_assets\meshes")
OUTPUT_DIR = os.path.join(PROJECT_DIR, r"converted_assets\meshes")
LOG_FILE = os.path.join(PROJECT_DIR, r"converted_assets\material_patch_log.txt")

# Enable addons
bpy.ops.preferences.addon_enable(module="io_scene_mw")
bpy.ops.preferences.addon_enable(module="tool_export_mesh")

# Load material mapping from CSV
import csv
mesh_mat_map = {}
csv_file = os.path.join(PROJECT_DIR, r"converted_assets\placement\seyda_neen_all_placements.csv")
with open(csv_file, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        obj = row["object_id"].strip().lower()
        mat = row.get("material_path", "").strip()
        if mat and obj not in mesh_mat_map:
            if mat.startswith("Data\\"):
                mat = mat[5:]
            mesh_mat_map[obj] = mat

print(f"Material mappings: {len(mesh_mat_map)}")

# Get all NIF files
nif_files = sorted([f for f in os.listdir(MESHES_DIR) if f.endswith(".nif")])
print(f"NIF files to process: {len(nif_files)}")

log_lines = []
success = 0
failed = 0
skipped = 0

for i, nif_name in enumerate(nif_files):
    mesh_name = nif_name.replace(".nif", "").lower()
    
    if mesh_name not in mesh_mat_map:
        skipped += 1
        continue
    
    mat_path = mesh_mat_map[mesh_name]
    nif_path = os.path.join(MESHES_DIR, nif_name)
    output_path = os.path.join(OUTPUT_DIR, nif_name)
    
    print(f"\n[{i+1}/{len(nif_files)}] {nif_name} -> {mat_path}")
    
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Import NIF using SGB importer
    try:
        bpy.ops.import_scene.custom_nif(filepath=nif_path)
    except Exception as e:
        msg = f"FAIL: {nif_name} - import failed: {e}"
        print(f"  {msg}")
        log_lines.append(msg)
        failed += 1
        continue
    
    # Set material path on root node
    root = bpy.context.active_object
    if root is None:
        for obj in bpy.context.scene.objects:
            if obj.type == 'EMPTY':
                root = obj
                bpy.context.view_layer.objects.active = root
                break
    
    if root is None:
        msg = f"FAIL: {nif_name} - no root object found"
        print(f"  {msg}")
        log_lines.append(msg)
        failed += 1
        continue
    
    # Set Import_Nif_Path so additive export works
    root["Import_Nif_Path"] = nif_path
    
    # Export with additive='Root' to modify the original NIF
    # and overwrite_material_paths=True to update material paths
    try:
        bpy.ops.export_scene.custom_nif(
            filepath=output_path,
            use_internal_geom_data=True,
            export_material=False,
            export_sf_mesh_hash_result=False,
            export_template='None',
            additive_export='Root',
            overwrite_material_paths=True,
        )
        msg = f"OK: {nif_name} -> {mat_path}"
        print(f"  {msg}")
        log_lines.append(msg)
        success += 1
    except Exception as e:
        msg = f"FAIL: {nif_name} - export failed: {e}"
        print(f"  {msg}")
        log_lines.append(msg)
        failed += 1

summary = f"\n{'='*60}\nMaterial patching complete!\nSuccess: {success}\nFailed: {failed}\nSkipped: {skipped}\nTotal: {len(nif_files)}\n"
print(summary)
log_lines.append(summary)

with open(LOG_FILE, "w") as f:
    f.write("\n".join(log_lines))
print(f"Log saved to: {LOG_FILE}")