"""Clone Havok + reshape AABB for structural meshes only, then regenerate full ESP."""
import os, sys, subprocess, csv, struct, io, math, shutil, json

NIF_DIR = r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind'
CLONE_SCRIPT = r'C:\Users\max\Projects\Morrowind\scripts\collision\clone_collision.py'
RESHAPE_SCRIPT = r'C:\Users\max\Projects\Morrowind\scripts\collision\reshape_collision.py'
PROJECT_DIR = r'C:\Users\max\Projects\Morrowind'

# Structural meshes that need Havok collision
STRUCTURAL = [
    'ex_nord_house_01', 'ex_nord_house_02', 'ex_nord_house_03',
    'ex_common_house_addon', 'ex_common_house_tall_01', 'ex_common_house_tall_02',
    'ex_common_lighthouse', 'in_common_lighthouse',
    'ex_de_docks_center', 'ex_de_docks_end', 'ex_de_docks_steps_01',
    'ex_de_shack_02', 'ex_de_shack_03', 'in_de_shack_02', 'in_de_shack_03',
    'ex_drystonewall_c_01', 'ex_drystonewall_end_01', 'ex_drystonewall_s_01',
    'ex_nord_chimney_01', 'ex_common_balcony_01', 'ex_common_skywalk_01',
    'ex_common_tower_thatch', 'in_common_tower_thatch',
    'ex_common_plat_cent', 'ex_common_plat_corn', 'ex_common_plat_end',
    'ex_nord_rock_01', 'ex_nord_rock_02',
    'terrain_rock_bc_12', 'terrain_rock_bc_13', 'terrain_rock_bc_14',
    'terrain_rock_bc_15', 'terrain_rock_bc_16', 'terrain_rock_bc_17', 'terrain_rock_bc_18',
    'in_nord_house_01', 'in_nord_house_02', 'in_nord_house_03',
    'in_nord_fireplace_01', 'in_c_pillar_wood',
    'in_c_stair_plain_tall_01', 'in_c_stair_plain_tall_02',
    'furn_de_firepit', 'furn_firepit00',
    'ex_de_railing_01', 'ex_de_railing_02', 'ex_de_railing_03',
    'ex_nord_door_01', 'ex_nord_doorf_01',
    'in_c_door_arched', 'in_c_djamb_plain_arched', 'in_c_djamb_stone_arched',
    'ex_ship_plank', 'ex_de_oar',
    'furn_log_01', 'furn_log_03', 'furn_log_04', 'light_logpile10',
    'flora_bc_tree_02', 'flora_bc_tree_04', 'flora_bc_tree_06',
    'flora_bc_tree_08', 'flora_bc_tree_09', 'flora_bc_tree_10',
    'flora_bc_tree_11', 'flora_bc_tree_12', 'flora_bc_tree_13',
    'flora_bc_log_01',
    'terrain_bc_scum_01', 'terrain_bc_scum_02', 'terrain_bc_scum_03',
]

def main():
    # Step 1: Clone Havok into structural meshes
    print("=== Step 1: Clone Havok ===")
    for mesh in STRUCTURAL:
        nif_path = os.path.join(NIF_DIR, mesh + '.nif')
        if not os.path.exists(nif_path):
            print(f"  SKIP {mesh}: NIF not found")
            continue
        result = subprocess.run(
            ['python', CLONE_SCRIPT, '--test', nif_path],
            capture_output=True, text=True, timeout=30
        )
        if 'OK' in result.stdout:
            print(f"  OK {mesh}")
        else:
            print(f"  FAIL {mesh}")

    # Step 2: Reshape to AABB boxes
    print("\n=== Step 2: Reshape AABB ===")
    for mesh in STRUCTURAL:
        nif_path = os.path.join(NIF_DIR, mesh + '.nif')
        if not os.path.exists(nif_path):
            continue
        result = subprocess.run(
            ['python', RESHAPE_SCRIPT, '--test', nif_path],
            capture_output=True, text=True, timeout=30
        )
        if 'OK' in result.stdout:
            print(f"  OK {mesh}")
        else:
            print(f"  FAIL {mesh}")

    # Step 3: Regenerate full ESP
    print("\n=== Step 3: Regenerate ESP ===")
    result = subprocess.run(
        ['python', os.path.join(PROJECT_DIR, 'scripts', 'generate_full_seydaneen.py')],
        capture_output=True, text=True, timeout=60
    )
    print(result.stdout[-500:] if result.stdout else "No output")
    if result.stderr:
        print(f"STDERR: {result.stderr[-500:]}")

    # Step 4: Deploy
    print("\n=== Step 4: Deploy ===")
    shutil.copy2(
        os.path.join(PROJECT_DIR, 'Data', 'SeydaNeen.esp'),
        r'C:\XboxGames\Starfield\Content\Data\SeydaNeen.esp'
    )
    print("Deployed SeydaNeen.esp")

    # Count Havok REFRs
    havok_count = 0
    with open(os.path.join(PROJECT_DIR, r'converted_assets\placement\seyda_neen_all_placements.csv')) as f:
        r = csv.DictReader(f)
        for row in r:
            obj = row['object_id'].strip().lower()
            if obj in STRUCTURAL:
                havok_count += 1
    print(f"Structural meshes: {len(STRUCTURAL)}")
    print(f"Havok REFRs in cell: {havok_count}")

if __name__ == "__main__":
    main()
