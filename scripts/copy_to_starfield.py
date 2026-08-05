"""
Copy converted assets to the Starfield Data folder.

This script copies all converted NIFs, .mat files, and textures
to the correct locations in the Starfield Data directory.

Run this BEFORE opening the Creation Kit.
"""

import os
import shutil

# Starfield Data folder (adjust if needed)
STARFIELD_DATA = r"C:\XboxGames\Starfield\Content\Data"

# Source directories
CONVERTED_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets"
MESH_SOURCE = os.path.join(CONVERTED_DIR, "meshes")
MAT_SOURCE = r"C:\Users\max\Projects\Morrowind\Data\Materials\morrowind"
TEXTURE_SOURCE = os.path.join(CONVERTED_DIR, "textures_upscaled")

# Destination directories
MESH_DEST = os.path.join(STARFIELD_DATA, "Meshes", "morrowind")
MAT_DEST = os.path.join(STARFIELD_DATA, "Materials", "morrowind")
TEXTURE_DEST = os.path.join(STARFIELD_DATA, "Textures", "morrowind")


def copy_directory(src, dst, label):
    """Copy directory contents recursively."""
    if not os.path.exists(src):
        print(f"  Source not found: {src}")
        return 0

    os.makedirs(dst, exist_ok=True)

    count = 0
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        dest_root = os.path.join(dst, rel_root)
        os.makedirs(dest_root, exist_ok=True)

        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(dest_root, f)
            shutil.copy2(src_file, dst_file)
            count += 1

    print(f"  Copied {count} files to {label}")
    return count


def main():
    print("=" * 60)
    print("COPYING ASSETS TO STARFIELD DATA FOLDER")
    print("=" * 60)
    print(f"Target: {STARFIELD_DATA}")
    print()

    if not os.path.exists(STARFIELD_DATA):
        print(f"ERROR: Starfield Data folder not found: {STARFIELD_DATA}")
        print("Please update STARFIELD_DATA in this script to match your installation.")
        return

    # Copy meshes (NIF files + geometries subdirectory)
    print("Copying meshes...")
    mesh_count = copy_directory(MESH_SOURCE, MESH_DEST, "Meshes\\morrowind")

    # Copy materials (.mat files)
    print("Copying materials...")
    mat_count = copy_directory(MAT_SOURCE, MAT_DEST, "Materials\\morrowind")

    # Copy textures (upscaled DDS files)
    print("Copying textures...")
    tex_count = copy_directory(TEXTURE_SOURCE, TEXTURE_DEST, "Textures\\morrowind")

    print()
    print("=" * 60)
    print("COPY COMPLETE")
    print("=" * 60)
    print(f"Meshes:   {mesh_count} files")
    print(f"Materials: {mat_count} files")
    print(f"Textures:  {tex_count} files")
    print()
    print("You can now open the Creation Kit and start placing assets.")
    print()
    print("Next steps:")
    print("1. Open Creation Kit")
    print("2. File -> Data -> Load 'Starfield.esm' as active")
    print("3. Also load 'TheElderStarSystem Magnus.esp' as optional")
    print("4. Create new plugin: 'SeydaNeen.esp'")
    print("5. Use placement CSVs in converted_assets/placement/ to place objects")


if __name__ == "__main__":
    main()
