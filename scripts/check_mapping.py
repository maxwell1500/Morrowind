import csv

with open(r"C:\Users\max\Projects\Morrowind\converted_assets\mapping\seyda_neen_asset_mapping.csv") as f:
    reader = csv.DictReader(f)
    converted = [r for r in reader if r["conversion_status"] == "complete"]
    print(f"Converted objects: {len(converted)}")
    print()
    print("Sample converted objects:")
    for r in converted[:5]:
        print(f"  {r['object_id']}: {r['nif_path']}, {r['primary_texture']}")
        print(f"    Meshes: {r['mesh_files_count']}, Mats: {r['mat_files_count']}")
        print(f"    Textures: {r['texture_count']}, Placement refs: {r['placement_count']}")
