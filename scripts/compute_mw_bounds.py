"""Compute bounding boxes for all Morrowind NIFs we use (including collision meshes).
Run with:
  & "tools\blender-3.6\blender-3.6.13-windows-x64\blender.exe" --background --python-expr "exec(open(r'C:\Users\max\Projects\Morrowind\scripts\compute_mw_bounds.py').read())"

Writes morrowind_mesh_bounds.json used by generate_full_seydaneen.py for OBND.
"""
import bpy
import os
import json
import csv

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")
MAPPING = os.path.join(PROJECT_DIR, r"converted_assets\mapping\seyda_neen_asset_mapping.csv")
OUTPUT = os.path.join(PROJECT_DIR, r"converted_assets\mapping\morrowind_mesh_bounds.json")

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

print(f"Found Morrowind NIFs for {len(mw_nifs)} meshes")

bounds = {}
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
            all_verts.append((world_v.x, world_v.y, world_v.z))

    if not all_verts:
        continue

    xs = [v[0] for v in all_verts]
    ys = [v[1] for v in all_verts]
    zs = [v[2] for v in all_verts]

    bounds[mesh_name] = {
        'min': [min(xs), min(ys), min(zs)],
        'max': [max(xs), max(ys), max(zs)],
        'nif': nif_path,
    }
    processed += 1

print(f"Computed bounds for {processed} meshes")

with open(OUTPUT, 'w') as f:
    json.dump(bounds, f, indent=2)

print(f"Saved to {OUTPUT}")
