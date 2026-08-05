"""
Phase 5: Generate Starfield .mat files and patch into converted NIFs.

Each unique Morrowind texture gets one .mat file that references the upscaled texture.
The .mat files are placed in Data/Materials/morrowind/ so the game can find them.

Then we use MeshConverter.EditNifBSGeometries to patch material paths into NIFs.
"""

import os
import sys
import json

# Add SGB to path
sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")

from MaterialConverter import MatFile, TextureIndex, ShaderModel

BASE_DIR = r"C:\Users\max\Projects\Morrowind"
CONVERTED_DIR = os.path.join(BASE_DIR, "converted_assets")
MESH_DIR = os.path.join(CONVERTED_DIR, "meshes")
TEXTURES_DIR = os.path.join(CONVERTED_DIR, "textures_upscaled")
MAT_DIR = os.path.join(BASE_DIR, "Data", "Materials", "morrowind")
TEXTURE_MAP_FILE = os.path.join(BASE_DIR, "raw_assets", "seyda_neen_textures.json")

# Starfield material paths are relative to game root
# e.g. "Data\Materials\morrowind\tx_wood_siding_01.mat"
GAME_MAT_PREFIX = "Data\\Materials\\morrowind\\"
GAME_TEX_PREFIX = "Data\\textures_upscaled\\"


def create_mat_file(texture_name, texture_path_rel):
    """Create a Starfield .mat file for a single texture."""
    mat = MatFile()
    mat.setName(texture_name)
    mat.setShaderModel(ShaderModel.ONE_LAYER_STANDARD)
    mat.setBaseID("0005DD03:A7CE75E1")
    
    # Set the color/diffuse texture
    mat.setTexturePath(TextureIndex.COLOR, texture_path_rel)
    
    return mat.compose()


def patch_nif_material(nif_path, mat_path_rel):
    """Patch a NIF file's material path using MeshConverter."""
    try:
        from MeshConverter import EditNifBSGeometries, ImportNifAsJson
        
        # Import NIF as JSON
        nif_json = ImportNifAsJson(nif_path, False, "")
        nif_data = json.loads(nif_json)
        
        # Find all BSGeometry nodes and update their mat_path
        def update_mat_paths(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "BSGeometry" or "BSGeometry" in str(obj.get("type", "")):
                    # Look for MATERIAL_PATH extra data
                    if "extraData" in obj:
                        for extra in obj["extraData"]:
                            if extra.get("name") == "MATERIAL_PATH":
                                extra["stringData"] = mat_path_rel
                    # Also set directly if present
                    if "mat_path" in obj:
                        obj["mat_path"] = mat_path_rel
                for v in obj.values():
                    update_mat_paths(v)
            elif isinstance(obj, list):
                for item in obj:
                    update_mat_paths(item)
        
        update_mat_paths(nif_data)
        
        # Write back the modified JSON
        modified_json = json.dumps(nif_data)
        
        # Use EditNifBSGeometries to apply changes
        output_path = nif_path  # overwrite
        assets_folder = os.path.dirname(nif_path)
        rtn = EditNifBSGeometries(nif_path, modified_json, output_path, assets_folder, True)
        
        return rtn.return_code == 0
    except Exception as e:
        print(f"  Error patching {os.path.basename(nif_path)}: {e}")
        return False


def main():
    # Load texture mapping
    with open(TEXTURE_MAP_FILE) as f:
        tex_data = json.load(f)
    
    textures_found = tex_data["textures_found"]
    mesh_texture_map = tex_data["mesh_texture_map"]
    
    # Create output directory
    os.makedirs(MAT_DIR, exist_ok=True)
    
    # ========================================
    # Step 1: Generate .mat files for all textures
    # ========================================
    print("=" * 60)
    print("STEP 1: Generating .mat files")
    print("=" * 60)
    
    mat_count = 0
    for tex_name, tex_path in textures_found.items():
        # Texture path in game relative format
        tex_game_path = GAME_TEX_PREFIX + tex_name + ".dds"
        
        mat_content = create_mat_file(tex_name, tex_game_path)
        mat_path = os.path.join(MAT_DIR, f"{tex_name}.mat")
        
        with open(mat_path, "w") as f:
            f.write(mat_content)
        mat_count += 1
    
    print(f"Created {mat_count} .mat files in {MAT_DIR}")
    
    # ========================================
    # Step 2: Create material mapping (mesh -> mat)
    # ========================================
    print("\n" + "=" * 60)
    print("STEP 2: Mapping meshes to materials")
    print("=" * 60)
    
    # For each mesh, determine which .mat to use
    # Use the first texture as the primary material
    mesh_mat_map = {}
    for mesh_name, textures in mesh_texture_map.items():
        if textures:
            primary_tex = textures[0]  # Use first texture as primary
            mat_path = GAME_MAT_PREFIX + primary_tex + ".mat"
            mesh_mat_map[mesh_name] = mat_path
    
    print(f"Mapped {len(mesh_mat_map)} meshes to materials")
    
    # ========================================
    # Step 3: Patch NIFs with material paths
    # ========================================
    print("\n" + "=" * 60)
    print("STEP 3: Patching NIFs with material paths")
    print("=" * 60)
    
    success = 0
    failed = 0
    skipped = 0
    
    nif_files = sorted([f for f in os.listdir(MESH_DIR) if f.endswith('.nif')])
    
    for nif_name in nif_files:
        mesh_name = nif_name.replace('.nif', '')
        
        if mesh_name not in mesh_mat_map:
            skipped += 1
            continue
        
        nif_path = os.path.join(MESH_DIR, nif_name)
        mat_path = mesh_mat_map[mesh_name]
        
        if patch_nif_material(nif_path, mat_path):
            success += 1
        else:
            failed += 1
    
    print(f"\nResults: {success} patched, {failed} failed, {skipped} skipped (no material mapping)")
    print(f"Total NIFs: {len(nif_files)}")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 60)
    print("PHASE 5 COMPLETE")
    print("=" * 60)
    print(f".mat files: {mat_count} created in {MAT_DIR}")
    print(f"NIF patches: {success} successful, {failed} failed")
    print(f"\nMaterial paths follow the pattern:")
    print(f"  {GAME_MAT_PREFIX}{{texture_name}}.mat")
    print(f"  e.g. {GAME_MAT_PREFIX}tx_wood_siding_01.mat")


if __name__ == "__main__":
    main()
