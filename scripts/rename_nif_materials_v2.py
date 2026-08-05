"""Import NIF, create material with correct path name, re-export."""
import bpy
import os
import csv

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MESHES_DIR = os.path.join(PROJECT_DIR, r"converted_assets\meshes")
OUTPUT_DIR = os.path.join(PROJECT_DIR, r"converted_assets\meshes")

bpy.ops.preferences.addon_enable(module="io_scene_mw")
bpy.ops.preferences.addon_enable(module="tool_export_mesh")

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

nif_files = sorted([f for f in os.listdir(MESHES_DIR) if f.endswith(".nif")])
print(f"Material mappings: {len(mesh_mat_map)}, NIFs: {len(nif_files)}")

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
    
    print(f"[{i+1}/{len(nif_files)}] {nif_name}")
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    try:
        bpy.ops.import_scene.custom_nif(filepath=nif_path)
    except Exception as e:
        print(f"  FAIL: import - {e}")
        failed += 1
        continue
    
    # Create a material with the correct path as its name
    mat = bpy.data.materials.new(name=mat_path)
    
    # Assign to all mesh objects
    assigned = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
            assigned += 1
    
    if assigned == 0:
        print(f"  FAIL: no mesh objects")
        failed += 1
        continue
    
    try:
        bpy.ops.export_scene.custom_nif(
            filepath=output_path,
            use_internal_geom_data=True,
            export_material=False,
            export_sf_mesh_hash_result=False,
            export_template='Auto',
        )
        print(f"  OK: {mat_path}")
        success += 1
    except Exception as e:
        print(f"  FAIL: export - {e}")
        failed += 1

print(f"\nResults: {success} OK, {failed} FAIL, {skipped} SKIP")