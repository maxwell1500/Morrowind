import json

with open(r"C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen_textures.json") as f:
    data = json.load(f)

# Show mesh_texture_map sample
for mesh_name, textures in list(data["mesh_texture_map"].items())[:5]:
    print(f"{mesh_name}: {textures}")

print(f"\nTotal meshes with textures: {data['total_meshes_with_textures']}")
print(f"Textures found: {len(data['textures_found'])}")
print(f"Textures missing: {len(data.get('textures_missing', {}))}")
