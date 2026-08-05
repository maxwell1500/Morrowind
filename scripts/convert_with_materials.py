"""Import with io_scene_mw (Morrowind), set material name, export with SGB."""
import bpy
import os
import csv

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")
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

def find_nif_file(mesh_name):
    for root, dirs, files in os.walk(MW_MESHES_DIR):
        for f in files:
            if f.lower() == (mesh_name.lower() + ".nif"):
                return os.path.join(root, f)
    for root, dirs, files in os.walk(MW_MESHES_DIR):
        for f in files:
            if f.lower().endswith(".nif") and mesh_name.lower() in f.lower():
                return os.path.join(root, f)
    return None

nif_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".nif")])
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
    output_path = os.path.join(OUTPUT_DIR, nif_name)
    
    # Find original Morrowind NIF
    mw_nif = find_nif_file(mesh_name)
    if mw_nif is None:
        print(f"  SKIP: {nif_name} - no original NIF found")
        skipped += 1
        continue
    
    print(f"[{i+1}/{len(nif_files)}] {nif_name}")
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Import with io_scene_mw (Morrowind import)
    try:
        bpy.ops.import_scene.mw(filepath=mw_nif)
    except Exception as e:
        print(f"  FAIL: import - {e}")
        failed += 1
        continue
    
    # Create material with correct path name
    mat = bpy.data.materials.new(name=mat_path)
    
    # Assign to all mesh objects
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
    
    # Delete collision objects
    to_delete = [obj for obj in bpy.context.scene.objects if obj.name.startswith('Collision')]
    if to_delete:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in to_delete:
            obj.select_set(True)
        bpy.ops.object.delete()
    
    # Ensure UV maps
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and len(obj.data.uv_layers) == 0:
            obj.data.uv_layers.new(name="UVMap")
    
    # Select root and children
    bpy.ops.object.select_all(action='DESELECT')
    root = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY' and not obj.name.startswith('Collision'):
            root = obj
            break
    if root is None:
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                root = obj
                break
    
    if root is None:
        print(f"  FAIL: no root")
        failed += 1
        continue
    
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    
    # Export with SGB
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