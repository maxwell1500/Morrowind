"""
Batch convert Morrowind NIFs to Starfield format.
Reads the Seyda Neen inventory and converts each unique mesh.

Run with: blender --background --python scripts/batch_convert_meshes.py
"""
import bpy
import os
import sys
import json
import shutil
import time

# Paths
PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, r"raw_assets\Morrowind_Full\meshes")
OUTPUT_DIR = os.path.join(PROJECT_DIR, r"converted_assets\meshes")
INVENTORY_FILE = os.path.join(PROJECT_DIR, r"raw_assets\seyda_neen_inventory.json")
LOG_FILE = os.path.join(PROJECT_DIR, r"converted_assets\conversion_log.txt")

# Enable addons
bpy.ops.preferences.addon_enable(module="io_scene_mw")
bpy.ops.preferences.addon_enable(module="tool_export_mesh")

def find_nif_file(mesh_name):
    """Find a .nif file by mesh name in the Morrowind meshes directory."""
    # Try exact name first
    for root, dirs, files in os.walk(MW_MESHES_DIR):
        for f in files:
            if f.lower() == (mesh_name.lower() + ".nif"):
                return os.path.join(root, f)
    # Try case-insensitive contains
    for root, dirs, files in os.walk(MW_MESHES_DIR):
        for f in files:
            if f.lower().endswith(".nif") and mesh_name.lower() in f.lower():
                return os.path.join(root, f)
    return None

def convert_nif(nif_path, output_dir, mesh_name):
    """Convert a single Morrowind NIF to Starfield format."""
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Import
    try:
        bpy.ops.import_scene.mw(filepath=nif_path)
    except Exception as e:
        return False, f"Import failed: {e}"

    # Find root empty or use first mesh as root
    root = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY' and not obj.name.startswith('Collision'):
            root = obj
            break

    if root is None:
        # No empty root, use the first mesh
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                root = obj
                break

    if root is None:
        return False, "No mesh objects found after import"

    # Delete collision and unwanted objects
    keep = set()
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and not obj.name.startswith('Object'):
            keep.add(obj.name)
        elif obj.type == 'EMPTY' and not obj.name.startswith('Collision'):
            keep.add(obj.name)

    to_delete = [obj for obj in bpy.context.scene.objects if obj.name not in keep]
    if to_delete:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in to_delete:
            obj.select_set(True)
        bpy.ops.object.delete()

    # Ensure UV maps on all meshes
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and len(obj.data.uv_layers) == 0:
            obj.data.uv_layers.new(name="UVMap")

    # Select root and children
    bpy.ops.object.select_all(action='DESELECT')
    if root.type == 'EMPTY':
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            if root.type != 'EMPTY':
                bpy.context.view_layer.objects.active = root
                root = obj  # Use first mesh as root

    # Export
    os.makedirs(output_dir, exist_ok=True)
    nif_output = os.path.join(output_dir, mesh_name + ".nif")

    try:
        bpy.ops.export_scene.custom_nif(
            filepath=nif_output,
            use_internal_geom_data=False,
            export_material=False,
            export_sf_mesh_hash_result=False,
            export_template='None'
        )
    except Exception as e:
        return False, f"Export failed: {e}"

    return True, nif_output

def main():
    # Load inventory
    with open(INVENTORY_FILE, "r") as f:
        inventory = json.load(f)

    # Get all unique mesh names from the inventory
    mesh_names = set()
    for cat in inventory.get("categories", {}).values():
        for item_id, count in cat:
            if cat == inventory.get("categories", {}).get("meshes", []):
                mesh_names.add(item_id)

    # Also include items that might have NIF files
    for cat_name, items in inventory.get("categories", {}).items():
        if cat_name in ("meshes", "items"):
            for item_id, count in items:
                mesh_names.add(item_id)

    # Add terrain/flora meshes
    for cat_name in ("other",):
        for item_id, count in inventory.get("categories", {}).get(cat_name, []):
            # Check if there's a corresponding NIF file
            if find_nif_file(item_id):
                mesh_names.add(item_id)

    print(f"Found {len(mesh_names)} unique mesh names to convert")

    # Clear output
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Log
    log_lines = []
    success_count = 0
    fail_count = 0
    skip_count = 0
    total = len(mesh_names)

    for i, mesh_name in enumerate(sorted(mesh_names)):
        print(f"\n[{i+1}/{total}] Converting: {mesh_name}")

        # Find NIF file
        nif_path = find_nif_file(mesh_name)
        if nif_path is None:
            print(f"  SKIP: No NIF file found")
            log_lines.append(f"SKIP: {mesh_name} - no NIF file found")
            skip_count += 1
            continue

        # Convert
        start = time.time()
        success, result = convert_nif(nif_path, OUTPUT_DIR, mesh_name)
        elapsed = time.time() - start

        if success:
            print(f"  OK ({elapsed:.1f}s): {result}")
            log_lines.append(f"OK: {mesh_name} -> {result} ({elapsed:.1f}s)")
            success_count += 1
        else:
            print(f"  FAIL: {result}")
            log_lines.append(f"FAIL: {mesh_name} - {result}")
            fail_count += 1

    # Summary
    summary = f"\n{'='*60}\nConversion complete!\n"
    summary += f"Success: {success_count}\nFailed: {fail_count}\nSkipped: {skip_count}\nTotal: {total}\n"
    print(summary)
    log_lines.append(summary)

    # Write log
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(log_lines))
    print(f"Log saved to: {LOG_FILE}")

    # List output
    print(f"\nOutput files:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for fn in files:
            fpath = os.path.join(root, fn)
            rel = os.path.relpath(fpath, OUTPUT_DIR)
            print(f"  {rel} ({os.path.getsize(fpath)} bytes)")

if __name__ == "__main__":
    main()
