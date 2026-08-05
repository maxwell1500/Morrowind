"""Test reading Morrowind NIF files with pyffi"""
import os
from pyffi.formats.nif import NifFormat

nif_dir = r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes"

target_files = []
for root, dirs, files in os.walk(nif_dir):
    for f in files:
        if f.lower().startswith("ex_nord") and f.lower().endswith(".nif"):
            target_files.append(os.path.join(root, f))
            if len(target_files) >= 3:
                break
    if len(target_files) >= 3:
        break

if not target_files:
    print("No ex_nord files found, searching for any NIF...")
    for root, dirs, files in os.walk(nif_dir):
        for f in files:
            if f.lower().endswith(".nif"):
                target_files.append(os.path.join(root, f))
                if len(target_files) >= 3:
                    break
        if len(target_files) >= 3:
            break

for fpath in target_files:
    print("Reading:", os.path.basename(fpath))
    data = NifFormat.Data()
    with open(fpath, "rb") as f:
        data.read(f)
    
    print("  Version:", data.version)
    print("  Blocks:", len(data.blocks))
    
    block_types = set()
    for block in data.blocks:
        block_types.add(type(block).__name__)
    print("  Block types:", block_types)
    
    geo_count = sum(1 for b in data.blocks if hasattr(b, "vertices"))
    print("  Geometry blocks:", geo_count)
    
    for block in data.blocks:
        if hasattr(block, "vertices") and hasattr(block, "triangles"):
            print("  First mesh vertices:", len(block.vertices))
            print("  First mesh triangles:", len(block.triangles))
            break
    print()
