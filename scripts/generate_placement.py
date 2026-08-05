"""
Phase 6: Generate Seyda Neen placement manifest for Creation Kit.

Extracts all object placements from the ESM JSON, converts coordinates
from Morrowind units to Starfield units, and outputs a CSV manifest
organized by cell for use in the Creation Kit.

Morrowind -> Starfield coordinate conversion:
- Morrowind uses units where 1 unit ≈ 0.5 cm (based on 1 cell = 192 units ≈ 96m)
- Starfield uses 1 unit = 1 cm
- Scale factor: multiply by ~0.5 (or more precisely, 0.5)
- Z axis: Morrowind Z is up, Starfield Z is up (same)
- Rotation: Morrowind uses Euler radians, Starfield uses ZYX Euler
"""

import json
import csv
import os
import math

ESM_PATH = r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind.json"
OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets\placement"
MESH_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes"
TEXTURE_MAP_PATH = r"C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen_textures.json"

# Scale factor: Morrowind units to Starfield units
# Morrowind: 1 cell = 192 units ≈ 96m → 1 unit ≈ 0.5m = 50cm
# Starfield: 1 unit = 1cm
# So scale = 50 (1 Morrowind unit = 50 Starfield units)
SCALE = 50.0

# Known mesh prefixes for filtering
MESH_PREFIXES = [
    "in_", "ex_", "furn_", "misc_", "light_", "active_", "door_",
    "de_", "imp_", "nor_", "bm_", "terrain_", "flora_", "barrel_",
    "com_", "gold_", "potion_", "pick_", "food_", "ingred_"
]


def is_mesh(obj_id):
    """Check if an object ID corresponds to a mesh we converted."""
    obj_lower = obj_id.lower()
    return any(obj_lower.startswith(p) for p in MESH_PREFIXES)


def convert_position(translation):
    """Convert Morrowind position to Starfield position."""
    x, y, z = translation
    return [x * SCALE, y * SCALE, z * SCALE]


def convert_rotation(rotation):
    """Convert Morrowind Euler rotation to Starfield ZYX Euler."""
    # Morrowind stores rotation as Euler angles in radians
    # Order appears to be Z, X, Y based on typical Bethesda convention
    if len(rotation) >= 3:
        rx, ry, rz = rotation
    else:
        rx, ry, rz = 0, 0, 0
    # Starfield uses degrees
    return [math.degrees(rx), math.degrees(ry), math.degrees(rz)]


def main():
    print("Loading Morrowind ESM JSON...")
    with open(ESM_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    # Load texture mapping for material info
    tex_data = None
    if os.path.exists(TEXTURE_MAP_PATH):
        with open(TEXTURE_MAP_PATH) as f:
            tex_data = json.load(f)

    # Find Seyda Neen cells
    seyda_cells = []
    for obj in data:
        if obj.get("type") == "Cell":
            name = obj.get("name", "")
            if "seyda" in name.lower():
                seyda_cells.append(obj)

    print(f"Found {len(seyda_cells)} Seyda Neen cells")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Track which meshes are actually placed
    placed_meshes = set()
    all_placements = []

    # Process each cell
    for cell_idx, cell in enumerate(seyda_cells):
        cell_name = cell["name"]
        refs = cell.get("references", [])

        # Sanitize cell name for filename
        safe_name = cell_name.replace(",", "").replace("'", "").replace(" ", "_")
        safe_name = safe_name.replace("__", "_").rstrip("_")

        cell_placements = []

        for ref in refs:
            obj_id = ref.get("id", "")
            if not is_mesh(obj_id):
                continue

            translation = ref.get("translation", [0, 0, 0])
            rotation = ref.get("rotation", [0, 0, 0])
            is_temporary = ref.get("temporary", False)
            destination = ref.get("destination", None)

            # Convert coordinates
            sf_pos = convert_position(translation)
            sf_rot = convert_rotation(rotation)

            # Determine material path
            mat_path = ""
            if tex_data and "mesh_texture_map" in tex_data:
                mesh_textures = tex_data["mesh_texture_map"].get(obj_id, [])
                if mesh_textures:
                    mat_path = f"Data\\Materials\\morrowind\\{mesh_textures[0]}.mat"

            # Check if mesh was actually converted
            mesh_converted = os.path.exists(os.path.join(MESH_DIR, f"{obj_id}.nif"))

            placement = {
                "cell": cell_name,
                "object_id": obj_id,
                "mesh_converted": mesh_converted,
                "x_mw": translation[0],
                "y_mw": translation[1],
                "z_mw": translation[2],
                "x_sf": sf_pos[0],
                "y_sf": sf_pos[1],
                "z_sf": sf_pos[2],
                "rot_x": sf_rot[0],
                "rot_y": sf_rot[1],
                "rot_z": sf_rot[2],
                "temporary": is_temporary,
                "material_path": mat_path,
                "destination_cell": destination.get("cell", "") if destination else "",
            }

            cell_placements.append(placement)
            all_placements.append(placement)
            if mesh_converted:
                placed_meshes.add(obj_id)

        # Write cell CSV
        csv_path = os.path.join(OUTPUT_DIR, f"cell_{cell_idx:02d}_{safe_name}.csv")
        with open(csv_path, "w", newline="") as f:
            if cell_placements:
                writer = csv.DictWriter(f, fieldnames=cell_placements[0].keys())
                writer.writeheader()
                writer.writerows(cell_placements)
            else:
                f.write(f"# No placeable meshes in {cell_name}\n")

        print(f"  {cell_name}: {len(cell_placements)} placeable objects -> {os.path.basename(csv_path)}")

    # Write master placement CSV
    master_csv = os.path.join(OUTPUT_DIR, "seyda_neen_all_placements.csv")
    with open(master_csv, "w", newline="") as f:
        if all_placements:
            writer = csv.DictWriter(f, fieldnames=all_placements[0].keys())
            writer.writeheader()
            writer.writerows(all_placements)

    # Write summary
    total_placeable = len(all_placements)
    total_converted = len(placed_meshes)
    total_not_converted = total_placeable - total_converted

    summary = {
        "total_cells": len(seyda_cells),
        "total_placements": total_placeable,
        "meshes_with_converted_nifs": total_converted,
        "meshes_without_converted_nifs": total_not_converted,
        "converted_mesh_list": sorted(list(placed_meshes)),
    }

    summary_path = os.path.join(OUTPUT_DIR, "placement_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"PLACEMENT MANIFEST COMPLETE")
    print(f"{'='*60}")
    print(f"Total cells: {len(seyda_cells)}")
    print(f"Total placeable objects: {total_placeable}")
    print(f"  With converted NIFs: {total_converted}")
    print(f"  Without converted NIFs: {total_not_converted}")
    print(f"\nOutput files in: {OUTPUT_DIR}")
    print(f"  - seyda_neen_all_placements.csv (master)")
    print(f"  - cell_XX_*.csv (per cell)")
    print(f"  - placement_summary.json")
    print(f"\nCoordinate conversion: Morrowind units × {SCALE} = Starfield units")
    print(f"  (1 Morrowind unit ≈ 0.5m → 50 Starfield cm units)")


if __name__ == "__main__":
    main()
