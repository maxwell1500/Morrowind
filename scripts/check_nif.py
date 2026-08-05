import os
import struct

nif_dir = r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\meshes"
# Get first few NIF files
nif_files = []
for root, dirs, files in os.walk(nif_dir):
    for f in files:
        if f.endswith(".nif"):
            nif_files.append(os.path.join(root, f))
            if len(nif_files) >= 3:
                break
    if len(nif_files) >= 3:
        break

for fpath in nif_files:
    print("File:", os.path.relpath(fpath, nif_dir))
    with open(fpath, "rb") as f:
        header = f.read(80)
    # Print hex dump of first 40 bytes
    hex_str = " ".join(f"{b:02x}" for b in header[:40])
    print("  Hex:", hex_str)
    # Try to find version string
    null_pos = header.find(b"\x00")
    if null_pos > 0 and null_pos < 40:
        print("  Version:", header[:null_pos].decode("ascii", errors="replace"))
    print()
