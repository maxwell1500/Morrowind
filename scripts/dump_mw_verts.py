"""Dump vertex data from all Morrowind NIFs via Blender import.
Run with:
  & "tools\blender-3.6\blender-3.6.13-windows-x64\blender.exe" --background --python-expr "exec(open(r'C:\Users\max\Projects\Morrowind\scripts\dump_mw_verts.py').read())"

Output: converted_assets/mapping/morrowind_mesh_verts.json
  Keyed by object_id, value = list of [x,y,z] float arrays
"""
import bpy
import os, json, csv, sys

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")
MAPPING = os.path.join(PROJECT_DIR, r"converted_assets\mapping\seyda_neen_asset_mapping.csv")
OUTPUT = os.path.join(PROJECT_DIR, r"converted_assets\mapping\morrowind_mesh_verts.json")

bpy.ops.preferences.addon_enable(module="io_scene_mw")

mesh_names = set()
with open(MAPPING, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('nif_converted', '').strip().lower() == 'true':
            mesh_names.add(row['object_id'].strip())

print(f"Found {len(mesh_names)} converted meshes")

mw_nifs = {}
for root, dirs, files in os.walk(MW_MESHES_DIR):
    for f in files:
        if not f.lower().endswith('.nif'):
            continue
        name_lower = f.lower()[:-4]
        for mn in mesh_names:
            if mn.lower() == name_lower:
                mw_nifs[mn] = os.path.join(root, f)
                break

print(f"Found {len(mw_nifs)} NIF files")

verts_data = {}
processed = 0
for mesh_name, nif_path in mw_nifs.items():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    try:
        bpy.ops.import_scene.mw(filepath=nif_path)
    except Exception as e:
        print(f"  SKIP: {mesh_name} - {e}")
        continue

    all_verts = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        m = obj.matrix_world
        for v in obj.data.vertices:
            world_v = m @ v.co
            all_verts.append([round(world_v.x, 4), round(world_v.y, 4), round(world_v.z, 4)])

    if not all_verts:
        print(f"  SKIP: {mesh_name} - no vertices")
        continue

    verts_data[mesh_name] = all_verts
    processed += 1
    if processed % 20 == 0:
        print(f"  ... {processed}/{len(mw_nifs)}")

print(f"Dumped vertices for {processed} meshes")

with open(OUTPUT, 'w') as f:
    json.dump(verts_data, f, separators=(',', ':'))

print(f"Saved to {OUTPUT} ({os.path.getsize(OUTPUT) // 1024} KB)")
