"""
Find textures referenced by Seyda Neen meshes.
Scans ORIGINAL Morrowind NIFs (not converted ones) for texture references.
"""
import os
import json
import re

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
MW_MESHES_DIR = os.path.join(PROJECT_DIR, "raw_assets", "Morrowind_Full", "meshes")
RAW_TEXTURES_DIR = os.path.join(PROJECT_DIR, "raw_assets", "Morrowind_Full", "textures")
INVENTORY_FILE = os.path.join(PROJECT_DIR, "raw_assets", "seyda_neen_inventory.json")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "raw_assets", "seyda_neen_textures.json")

def find_texture_files(textures_dir):
    """Build a lookup of texture filenames (lowercase) -> full paths."""
    lookup = {}
    for root, dirs, files in os.walk(textures_dir):
        for f in files:
            if f.lower().endswith(".dds"):
                name = os.path.splitext(f)[0].lower()
                lookup[name] = os.path.join(root, f)
    return lookup

def find_nif_file(mesh_name, meshes_dir):
    """Find a .nif file by mesh name."""
    for root, dirs, files in os.walk(meshes_dir):
        for f in files:
            if f.lower() == (mesh_name.lower() + ".nif"):
                return os.path.join(root, f)
    return None

def scan_nif_for_textures(nif_path):
    """Scan a Morrowind NIF for texture references."""
    textures = set()
    try:
        with open(nif_path, "rb") as f:
            data = f.read()
        # Find .tga and .dds references
        for match in re.finditer(rb'([a-zA-Z0-9_\\/.]+\.tga)', data):
            tex_path = match.group(1).decode("ascii", errors="ignore")
            tex_name = os.path.splitext(os.path.basename(tex_path))[0].lower()
            textures.add(tex_name)
        for match in re.finditer(rb'([a-zA-Z0-9_\\/.]+\.dds)', data):
            tex_path = match.group(1).decode("ascii", errors="ignore")
            tex_name = os.path.splitext(os.path.basename(tex_path))[0].lower()
            textures.add(tex_name)
    except:
        pass
    return textures

def main():
    # Load inventory
    with open(INVENTORY_FILE, "r") as f:
        inventory = json.load(f)
    
    # Get all mesh names
    mesh_names = set()
    for cat_name, items in inventory.get("categories", {}).items():
        for item_id, count in items:
            mesh_names.add(item_id)
    
    # Build texture lookup
    print("Building texture lookup...")
    tex_lookup = find_texture_files(RAW_TEXTURES_DIR)
    print(f"Found {len(tex_lookup)} DDS textures in raw_assets")
    
    # Scan original Morrowind NIFs
    print("\nScanning original Morrowind NIFs for texture references...")
    all_textures = set()
    mesh_texture_map = {}
    
    for mesh_name in sorted(mesh_names):
        nif_path = find_nif_file(mesh_name, MW_MESHES_DIR)
        if nif_path:
            textures = scan_nif_for_textures(nif_path)
            if textures:
                mesh_texture_map[mesh_name] = sorted(textures)
                all_textures.update(textures)
    
    print(f"Found {len(all_textures)} unique texture references across {len(mesh_texture_map)} meshes")
    
    # Check which textures we have
    found = {}
    missing = {}
    for tex in all_textures:
        if tex in tex_lookup:
            found[tex] = tex_lookup[tex]
        else:
            missing[tex] = None
    
    print(f"\nTextures found in raw_assets: {len(found)}")
    print(f"Textures MISSING from raw_assets: {len(missing)}")
    
    if found:
        print("\nFound textures (sample):")
        for tex, path in sorted(found.items())[:15]:
            size = os.path.getsize(path)
            print(f"  {tex}.dds ({size} bytes)")
    
    if missing:
        print("\nMissing textures:")
        for tex in sorted(missing):
            # Check for partial matches
            matches = [k for k in tex_lookup if tex in k or k in tex][:3]
            if matches:
                print(f"  {tex} -> possible: {matches}")
            else:
                print(f"  {tex}")
    
    # Save results
    results = {
        "total_textures_referenced": len(all_textures),
        "textures_found": {k: v for k, v in sorted(found.items())},
        "textures_missing": sorted(missing.keys()),
        "mesh_texture_map": mesh_texture_map,
        "total_meshes_with_textures": len(mesh_texture_map)
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
