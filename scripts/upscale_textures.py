"""
Upscale converted textures using RealESRGAN.
Pipeline: DDS -> PNG (ImageMagick) -> upscale (RealESRGAN) -> DDS (texconv)
"""
import os
import subprocess
import shutil
import glob

PROJECT_DIR = r"C:\Users\max\Projects\Morrowind"
CONVERTED_TEXTURES = os.path.join(PROJECT_DIR, "converted_assets", "textures")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "converted_assets", "textures_upscaled")
TEMP_DIR = os.path.join(PROJECT_DIR, "converted_assets", "upscale_temp")
MAGICK = r"C:\Users\max\AppData\Local\Microsoft\WinGet\Links\magick.exe"
REALESRGAN = r"C:\Users\max\scoop\apps\realesrgan-ncnn-vulkan\current\realesrgan-ncnn-vulkan.exe"
TEXCONV = r"C:\Users\max\AppData\Local\Microsoft\WinGet\Links\texconv.exe"

UPSCALE_FACTOR = 2  # 2x upscale
MODEL = "realesrgan-x4plus"

def main():
    # Get all converted textures
    dds_files = glob.glob(os.path.join(CONVERTED_TEXTURES, "*.dds"))
    print(f"Found {len(dds_files)} textures to upscale")
    
    # Clean temp/output
    for d in [TEMP_DIR, OUTPUT_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)
    
    png_dir = os.path.join(TEMP_DIR, "png")
    upscaled_dir = os.path.join(TEMP_DIR, "upscaled")
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(upscaled_dir, exist_ok=True)
    
    success = 0
    failed = 0
    
    for i, dds_path in enumerate(dds_files):
        name = os.path.splitext(os.path.basename(dds_path))[0]
        print(f"[{i+1}/{len(dds_files)}] {name}...", end=" ", flush=True)
        
        png_path = os.path.join(png_dir, name + ".png")
        upscaled_png = os.path.join(upscaled_dir, name + ".png")
        final_dds = os.path.join(OUTPUT_DIR, name + ".dds")
        
        try:
            # Step 1: DDS -> PNG
            r = subprocess.run([MAGICK, "convert", dds_path, png_path], capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(png_path):
                print(f"FAIL (DDS->PNG): {r.stderr[:100]}")
                failed += 1
                continue
            
            # Step 2: Upscale with RealESRGAN
            r = subprocess.run([REALESRGAN, "-i", png_path, "-o", upscaled_png, "-n", MODEL, "-s", str(UPSCALE_FACTOR)], capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(upscaled_png):
                print(f"FAIL (upscale): {r.stderr[:100]}")
                failed += 1
                continue
            
            # Step 3: PNG -> DDS (BC3_UNORM for Starfield)
            r = subprocess.run([TEXCONV, "-f", "BC3_UNORM", "-m", "0", "-o", OUTPUT_DIR, upscaled_png], capture_output=True, text=True)
            if r.returncode != 0:
                # Try BC1 if BC3 fails (no alpha textures)
                r = subprocess.run([TEXCONV, "-f", "BC1_UNORM", "-m", "0", "-o", OUTPUT_DIR, upscaled_png], capture_output=True, text=True)
            
            if os.path.exists(final_dds):
                size = os.path.getsize(final_dds)
                print(f"OK ({size} bytes)")
                success += 1
            else:
                # Check if texconv put it in a subdirectory
                possible = os.path.join(OUTPUT_DIR, os.path.basename(upscaled_png).replace('.png', '.dds'))
                if os.path.exists(possible):
                    size = os.path.getsize(possible)
                    print(f"OK ({size} bytes)")
                    success += 1
                else:
                    print(f"FAIL (PNG->DDS)")
                    failed += 1
        
        except Exception as e:
            print(f"FAIL: {e}")
            failed += 1
    
    print(f"\nUpscale complete: {success} success, {failed} failed")
    
    # Cleanup temp
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    main()
