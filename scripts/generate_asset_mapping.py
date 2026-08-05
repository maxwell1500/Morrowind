"""
Generate comprehensive Seyda Neen asset mapping spreadsheet.

Maps every Morrowind object to its converted Starfield assets:
- NIF files
- .mesh files
- .mat files
- Textures (original and upscaled)

Input sources:
- seyda_neen_inventory.json (471 unique objects)
- seyda_neen_textures.json (mesh-to-texture mapping)
- converted_assets/meshes/ (242 converted NIFs)
- Data/Materials/morrowind/ (179 .mat files)
- converted_assets/textures_upscaled/ (179 upscaled textures)
"""

import os
import json
import csv

BASE_DIR = r"C:\Users\max\Projects\Morrowind"
CONVERTED_DIR = os.path.join(BASE_DIR, "converted_assets")
MESH_DIR = os.path.join(CONVERTED_DIR, "meshes")
GEO_DIR = os.path.join(MESH_DIR, "geometries")
MAT_DIR = os.path.join(BASE_DIR, "Data", "Materials", "morrowind")
TEX_ORIG_DIR = os.path.join(BASE_DIR, "raw_assets", "Morrowind_Full", "textures")
TEX_UPSCALED_DIR = os.path.join(CONVERTED_DIR, "textures_upscaled")
OUTPUT_DIR = os.path.join(CONVERTED_DIR, "mapping")
PLACEMENT_DIR = os.path.join(CONVERTED_DIR, "placement")


def load_inventory():
    """Load the Seyda Neen inventory."""
    with open(os.path.join(BASE_DIR, "raw_assets", "seyda_neen_inventory.json")) as f:
        data = json.load(f)
    return data


def load_texture_map():
    """Load the mesh-to-texture mapping."""
    with open(os.path.join(BASE_DIR, "raw_assets", "seyda_neen_textures.json")) as f:
        data = json.load(f)
    return data


def load_placement_summary():
    """Load the placement summary."""
    summary_path = os.path.join(PLACEMENT_DIR, "placement_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            return json.load(f)
    return {}


def load_cell_placements():
    """Load all cell placement CSVs."""
    placements = {}
    for fname in os.listdir(PLACEMENT_DIR):
        if fname.endswith('.csv') and fname.startswith('cell_'):
            csv_path = os.path.join(PLACEMENT_DIR, fname)
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj_id = row['object_id']
                    if obj_id not in placements:
                        placements[obj_id] = []
                    placements[obj_id].append(row)
    return placements


def check_nif_exists(obj_id):
    """Check if a converted NIF exists for this object."""
    nif_path = os.path.join(MESH_DIR, f"{obj_id}.nif")
    return os.path.exists(nif_path), nif_path if os.path.exists(nif_path) else ""


def check_mesh_files(obj_id):
    """Check for .mesh files in the geometries directory."""
    mesh_files = []
    geo_dir = os.path.join(GEO_DIR, obj_id)
    if os.path.isdir(geo_dir):
        for f in os.listdir(geo_dir):
            if f.endswith('.mesh'):
                mesh_files.append(os.path.join(geo_dir, f))
    return mesh_files


def check_mat_exists(obj_id, textures):
    """Check if .mat files exist for this object's textures."""
    mat_files = []
    for tex_name in textures:
        mat_path = os.path.join(MAT_DIR, f"{tex_name}.mat")
        if os.path.exists(mat_path):
            mat_files.append(mat_path)
    return mat_files


def check_texture_exists(tex_name):
    """Check if upscaled texture exists."""
    upscaled = os.path.join(TEX_UPSCALED_DIR, f"{tex_name}.dds")
    original = os.path.join(TEX_ORIG_DIR, f"{tex_name}.dds")
    return os.path.exists(upscaled), os.path.exists(original)


def get_file_size(filepath):
    """Get file size in bytes."""
    return os.path.getsize(filepath) if os.path.exists(filepath) else 0


def main():
    print("Loading data sources...")
    inventory = load_inventory()
    tex_map = load_texture_map()
    placement_summary = load_placement_summary()
    cell_placements = load_cell_placements()

    objects = inventory.get("objects", {})
    categories = inventory.get("categories", {})
    mesh_texture_map = tex_map.get("mesh_texture_map", {})
    textures_found = tex_map.get("textures_found", {})
    converted_mesh_list = set(placement_summary.get("converted_mesh_list", []))

    print(f"Objects: {len(objects)}")
    print(f"Textures: {len(textures_found)}")
    print(f"Mesh-texture mappings: {len(mesh_texture_map)}")
    print(f"Converted meshes: {len(converted_mesh_list)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ========================================
    # Spreadsheet 1: Complete Object Mapping
    # ========================================
    print("\nGenerating object mapping spreadsheet...")

    rows = []
    for obj_id, ref_count in sorted(objects.items()):
        # Determine category
        category = "unknown"
        for cat, items in categories.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, list) and len(item) >= 2 and item[0] == obj_id:
                        category = cat
                        break
                # Also check tuples
                for item in items:
                    if isinstance(item, (list, tuple)) and len(item) >= 2 and item[0] == obj_id:
                        category = cat
                        break

        # Check NIF conversion
        nif_converted, nif_path = check_nif_exists(obj_id)

        # Check mesh files
        mesh_files = check_mesh_files(obj_id)
        mesh_count = len(mesh_files)

        # Get texture info
        textures = mesh_texture_map.get(obj_id, [])
        primary_texture = textures[0] if textures else ""

        # Check .mat files
        mat_files = check_mat_exists(obj_id, textures)
        mat_count = len(mat_files)

        # Check texture status
        primary_tex_upscaled = False
        primary_tex_original = False
        if primary_texture:
            primary_tex_upscaled, primary_tex_original = check_texture_exists(primary_texture)

        # Get file sizes
        nif_size = get_file_size(nif_path)
        mat_size = sum(get_file_size(m) for m in mat_files)
        total_mesh_size = sum(get_file_size(m) for m in mesh_files)

        # Get placement count
        placement_count = len(cell_placements.get(obj_id, []))

        rows.append({
            "object_id": obj_id,
            "category": category,
            "reference_count": ref_count,
            "placement_count": placement_count,
            "nif_converted": nif_converted,
            "nif_path": f"meshes\\{obj_id}.nif" if nif_converted else "",
            "nif_size_bytes": nif_size,
            "mesh_files_count": mesh_count,
            "mesh_total_size_bytes": total_mesh_size,
            "primary_texture": primary_texture,
            "all_textures": "; ".join(textures),
            "texture_count": len(textures),
            "mat_files_count": mat_count,
            "primary_mat": f"Materials\\morrowind\\{primary_texture}.mat" if primary_texture else "",
            "primary_tex_upscaled": primary_tex_upscaled,
            "primary_tex_original": primary_tex_original,
            "conversion_status": "complete" if nif_converted and primary_texture else
                                 "partial" if nif_converted else "not_converted",
        })

    csv_path = os.path.join(OUTPUT_DIR, "seyda_neen_asset_mapping.csv")
    with open(csv_path, "w", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"  Written to {os.path.basename(csv_path)} ({len(rows)} objects)")

    # ========================================
    # Spreadsheet 2: Texture Mapping
    # ========================================
    print("\nGenerating texture mapping spreadsheet...")

    tex_rows = []
    for tex_name, tex_path in sorted(textures_found.items()):
        upscaled_exists, original_exists = check_texture_exists(tex_name)

        # Find which meshes use this texture
        using_meshes = []
        for mesh_name, mesh_textures in mesh_texture_map.items():
            if tex_name in mesh_textures:
                using_meshes.append(mesh_name)

        mat_path = os.path.join(MAT_DIR, f"{tex_name}.mat")
        mat_exists = os.path.exists(mat_path)

        upscaled_size = get_file_size(os.path.join(TEX_UPSCALED_DIR, f"{tex_name}.dds"))
        original_size = get_file_size(os.path.join(TEX_ORIG_DIR, f"{tex_name}.dds"))

        tex_rows.append({
            "texture_name": tex_name,
            "original_path": tex_path if original_exists else "",
            "original_exists": original_exists,
            "original_size_bytes": original_size,
            "upscaled_path": f"textures_upscaled\\{tex_name}.dds" if upscaled_exists else "",
            "upscaled_exists": upscaled_exists,
            "upscaled_size_bytes": upscaled_size,
            "mat_exists": mat_exists,
            "mat_path": f"Materials\\morrowind\\{tex_name}.mat" if mat_exists else "",
            "used_by_mesh_count": len(using_meshes),
            "used_by_meshes": "; ".join(sorted(using_meshes)[:10]),
        })

    tex_csv_path = os.path.join(OUTPUT_DIR, "texture_mapping.csv")
    with open(tex_csv_path, "w", newline="") as f:
        if tex_rows:
            writer = csv.DictWriter(f, fieldnames=tex_rows[0].keys())
            writer.writeheader()
            writer.writerows(tex_rows)

    print(f"  Written to {os.path.basename(tex_csv_path)} ({len(tex_rows)} textures)")

    # ========================================
    # Spreadsheet 3: Summary Statistics
    # ========================================
    print("\nGenerating summary statistics...")

    # Count by category
    cat_counts = {}
    for row in rows:
        cat = row["category"]
        if cat not in cat_counts:
            cat_counts[cat] = {"total": 0, "converted": 0, "not_converted": 0}
        cat_counts[cat]["total"] += 1
        if row["conversion_status"] == "complete":
            cat_counts[cat]["converted"] += 1
        else:
            cat_counts[cat]["not_converted"] += 1

    # Count conversion status
    status_counts = {"complete": 0, "partial": 0, "not_converted": 0}
    for row in rows:
        status_counts[row["conversion_status"]] += 1

    # File size totals
    total_nif_size = sum(r["nif_size_bytes"] for r in rows)
    total_mat_size = sum(r["mat_files_count"] for r in rows) * 1000  # estimate
    total_tex_upscaled = sum(
        get_file_size(os.path.join(TEX_UPSCALED_DIR, f"{t}.dds"))
        for t in textures_found.keys()
    )

    summary = {
        "object_mapping": {
            "total_objects": len(rows),
            "by_category": cat_counts,
            "by_status": status_counts,
        },
        "texture_mapping": {
            "total_textures": len(tex_rows),
            "upscaled_count": sum(1 for r in tex_rows if r["upscaled_exists"]),
            "mat_count": sum(1 for r in tex_rows if r["mat_exists"]),
        },
        "file_sizes": {
            "total_nif_bytes": total_nif_size,
            "total_tex_upscaled_bytes": total_tex_upscaled,
        },
    }

    summary_path = os.path.join(OUTPUT_DIR, "mapping_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Written to {os.path.basename(summary_path)}")

    # ========================================
    # Final Summary
    # ========================================
    print(f"\n{'='*60}")
    print(f"ASSET MAPPING COMPLETE")
    print(f"{'='*60}")
    print(f"\nObjects: {len(rows)} total")
    print(f"  Converted:    {status_counts['complete']}")
    print(f"  Partial:      {status_counts['partial']}")
    print(f"  Not converted: {status_counts['not_converted']}")
    print(f"\nTextures: {len(tex_rows)} total")
    print(f"  Upscaled:     {summary['texture_mapping']['upscaled_count']}")
    print(f"  With .mat:    {summary['texture_mapping']['mat_count']}")
    print(f"\nOutput files in: {OUTPUT_DIR}")
    print(f"  - seyda_neen_asset_mapping.csv (all objects)")
    print(f"  - texture_mapping.csv (all textures)")
    print(f"  - mapping_summary.json (statistics)")


if __name__ == "__main__":
    main()
