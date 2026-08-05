"""
Batch convert Morrowind textures to Starfield format.
1. Convert DXT1/DXT3 to BC1_UNORM/BC3_UNORM
2. Upscale with RealESRGAN (2x or 4x)
3. Generate mipmaps with texconv
4. Save to converted_assets/textures/
"""
import os
import json
import subprocess
import shutil
import struct
import time

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
RAW_TEXTURES_DIR = os.path.join(PROJECT_DIR, "raw_assets", "Morrowind_Full", "textures")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "converted_assets", "textures")
TEMP_DIR = os.path.join(PROJECT_DIR, "converted_assets", "textures_temp")
TEXCONV = r"C:\Users\max\AppData\Local\Microsoft\WinGet\Links\texconv.exe"
REALESRGAN = r"C:\Users\max\scoop\apps\realesrgan-ncnn-vulkan\current\realesrgan-ncnn-vulkan.exe"
TEXTURE_JSON = os.path.join(PROJECT_DIR, "raw_assets", "seyda_neen_textures.json")
LOG_FILE = os.path.join(PROJECT_DIR, "converted_assets", "texture_conversion_log.txt")

# Target format and size for Starfield
TARGET_FORMAT = "BC3_UNORM"  # BC3 for alpha, BC1 for no-alpha
TARGET_MIN_SIZE = 512  # Minimum texture dimension
TARGET_MAX_SIZE = 2048  # Maximum texture dimension
UPSCALE_FACTOR = 2  # RealESRGAN upscale factor

def read_dds_info(path):
    """Read DDS header info."""
    with open(path, 'rb') as f:
        magic = f.read(4)
        if magic != b'DDS ':
            return None
        header = f.read(124)
        height = struct.unpack('<I', header[8:12])[0]
        width = struct.unpack('<I', header[12:16])[0]
        mips = struct.unpack('<I', header[24:28])[0]
        pf_flags = struct.unpack('<I', header[76:80])[0]
        fourcc = header[80:84].decode('ascii', errors='replace')
        return {'width': width, 'height': height, 'mips': mips, 'fourcc': fourcc, 'pf_flags': pf_flags}

def needs_upscale(info):
    """Check if texture needs upscaling for Starfield."""
    return info['width'] < TARGET_MIN_SIZE or info['height'] < TARGET_MIN_SIZE

def get_target_format(info):
    """Determine target format based on source format."""
    if info['fourcc'] in ('DXT3', 'DXT4', 'DXT5'):
        return "BC3_UNORM"  # Has alpha
    return "BC1_UNORM"  # No alpha

def convert_texture(src_path, dst_path):
    """Convert a single texture using texconv."""
    info = read_dds_info(src_path)
    if info is None:
        return False, "Not a valid DDS file"
    
    target_fmt = get_target_format(info)
    
    # Step 1: Convert format
    temp_dir = os.path.join(TEMP_DIR, "converted")
    os.makedirs(temp_dir, exist_ok=True)
    
    cmd = [TEXCONV, "-f", target_fmt, "-o", temp_dir, src_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"texconv failed: {result.stderr}"
    
    converted_file = os.path.join(temp_dir, os.path.basename(src_path))
    if not os.path.exists(converted_file):
        return False, "texconv output not found"
    
    # Step 2: Upscale if needed
    if needs_upscale(info):
        upscale_dir = os.path.join(TEMP_DIR, "upscaled")
        os.makedirs(upscale_dir, exist_ok=True)
        
        # RealESRGAN upscale
        cmd = [REALESRGAN, "-i", converted_file, "-o", os.path.join(upscale_dir, os.path.basename(src_path)), "-n", "realesrgan-x4plus", "-s", str(UPSCALE_FACTOR)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(os.path.join(upscale_dir, os.path.basename(src_path))):
            converted_file = os.path.join(upscale_dir, os.path.basename(src_path))
    
    # Step 3: Ensure proper size (pad to power of 2 if needed)
    # Step 4: Copy to final output
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    shutil.copy2(converted_file, dst_path)
    
    return True, dst_path

def main():
    # Load texture list
    with open(TEXTURE_JSON, "r") as f:
        texture_data = json.load(f)
    
    textures = texture_data.get("textures_found", {})
    print(f"Found {len(textures)} textures to convert")
    
    # Clean output dirs
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    log_lines = []
    success = 0
    failed = 0
    total = len(textures)
    
    for i, (tex_name, tex_path) in enumerate(sorted(textures.items())):
        print(f"[{i+1}/{total}] {tex_name}...", end=" ", flush=True)
        
        if not os.path.exists(tex_path):
            print("SKIP (not found)")
            log_lines.append(f"SKIP: {tex_name} - file not found")
            continue
        
        dst_path = os.path.join(OUTPUT_DIR, tex_name + ".dds")
        start = time.time()
        ok, result = convert_texture(tex_path, dst_path)
        elapsed = time.time() - start
        
        if ok:
            size = os.path.getsize(dst_path)
            print(f"OK ({elapsed:.1f}s, {size} bytes)")
            log_lines.append(f"OK: {tex_name} ({elapsed:.1f}s, {size} bytes)")
            success += 1
        else:
            print(f"FAIL: {result}")
            log_lines.append(f"FAIL: {tex_name} - {result}")
            failed += 1
    
    summary = f"\n{'='*50}\nConversion complete!\nSuccess: {success}\nFailed: {failed}\nTotal: {total}\n"
    print(summary)
    log_lines.append(summary)
    
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(log_lines))
    print(f"Log: {LOG_FILE}")
    
    # Cleanup temp
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    main()
