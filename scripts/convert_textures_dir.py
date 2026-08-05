"""Convert textures in a specified directory from BC3 to BC7."""
import os
import subprocess
import shutil
import tempfile
import sys

TEXTURES_DIR = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\max\Projects\Morrowind\converted_assets\textures"
TEXCONV = r"C:\Users\max\AppData\Local\Microsoft\WinGet\Links\texconv.exe"

def convert_texture(path):
    fname = os.path.basename(path)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_src = os.path.join(tmpdir, fname)
        shutil.copy2(path, tmp_src)
        cmd = [TEXCONV, "-f", "BC7_UNORM_SRGB", "-m", "0", "-y",
               tmp_src, "-o", tmpdir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return False, result.stderr[:200]
        shutil.copy2(tmp_src, path)
    return True, ""

def main():
    dds_files = sorted([f for f in os.listdir(TEXTURES_DIR) if f.lower().endswith('.dds')])
    print(f"Found {len(dds_files)} DDS files in {TEXTURES_DIR}")
    converted = 0
    failed = 0
    for i, f in enumerate(dds_files):
        path = os.path.join(TEXTURES_DIR, f)
        if i % 20 == 0:
            print(f"  [{i+1}/{len(dds_files)}] {f}...")
        ok, err = convert_texture(path)
        if ok:
            converted += 1
        else:
            failed += 1
            print(f"  FAILED: {f}: {err}")
    print(f"Done: {converted} converted, {failed} failed")

if __name__ == "__main__":
    main()
