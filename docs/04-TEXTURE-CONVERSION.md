# Phase 4: Texture Conversion & Upscaling

**Estimated Time:** 10-20 hours
**Prerequisites:** Phase 2 complete, chaiNNer/GIMP/texconv installed

## Overview

Morrowind textures are tiny (64x64 to 256x256). Starfield needs 2K-4K.
We upscale using AI, convert to correct DDS format, and set up materials.

## Understanding Texture Formats

### Morrowind Textures
- Resolution: 64x64 to 256x256 (most are 64x64 or 128x128)
- Format: DDS (DXT1 for opaque, DXT5 for alpha) or TGA
- Color space: sRGB
- Compression: DXT1 (4:1 ratio), DXT5 (4:1 ratio with alpha)

### Starfield Textures
- Resolution: 1K to 4K (2048x2048 or 4096x4096 typical)
- Format: DDS with specific DXGI formats
- Color space: sRGB for color, Linear for data
- Compression: BC1 (DXT1), BC3 (DXT5), BC7 (better quality)

### Required DDS Formats for Starfield

| Texture Type | Format | Color Space |
|--------------|--------|-------------|
| Color/Diffuse | R8G8B8A8_UNORM_SRGB or BC7_UNORM_SRGB | sRGB |
| Normal map | R8G8B8A8_UNORM or BC5_UNORM | Linear |
| Roughness | R8_UNORM or BC4_UNORM | Linear |
| Metalness | R8_UNORM or BC4_UNORM | Linear |
| Emissive | R8G8B8A8_UNORM_SRGB | sRGB |

**For simplicity:** Start with R8G8B8A8_UNORM_SRGB (uncompressed) for color
textures. You can optimize to BC7 later for performance.

## Step 4.1: Identify All Required Textures

For each converted mesh, identify its texture references:

1. Open the original Morrowind NIF in NifSkope
2. Find the NiTexturingProperty node
3. Note the texture path(s)
4. These should have been extracted in Phase 2

**Seyda Neen texture categories:**

| Category | Example Files | Count |
|----------|--------------|-------|
| Ground/Terrain | tx_bitter_coast_*, tx_mud_* | ~10 |
| Imperial buildings | tx_imp_wall_*, tx_imp_roof_* | ~15 |
| Dunmer buildings | tx_dun_wall_*, tx_dun_roof_* | ~10 |
| Furniture | tx_furn_* | ~5 |
| Clutter | tx_barrel_*, tx_crate_* | ~5 |
| Water | tx_water_* | ~3 |
| Vegetation | tx_grass_*, tx_bush_* | ~5 |
| **Total** | | **~53** |

## Step 4.2: Choose Upscaling Method

### Option A: Use Existing Upscaled Pack (Recommended Start)

**Morrowind Enhanced Textures (MET)** - nexusmods.com/morrowind/mods/46221

This pack already has AI-upscaled versions of many base game textures.
Using MET as a starting point saves significant time.

**Pros:**
- Already upscaled to 2K
- Community-tested quality
- Covers most base game textures

**Cons:**
- May not cover all Seyda Neen-specific textures
- Some textures may not match your desired style
- Still needs DDS format conversion

**Usage:**
1. Download MET from Nexus
2. Extract to a temporary folder
3. Find matching textures for your meshes
4. Convert to Starfield DDS format (Step 4.5)

### Option B: AI Upscale from Scratch

Use chaiNNer with ESRGAN models to upscale original Morrowind textures.

**Recommended chaiNNer Workflow:**

1. **Launch chaiNNer**
2. **Create a new chain:**

```
Load Image → Upscale Model (RealESRGAN_x4plus) → Save Image
```

3. **Settings:**
   - Upscale model: RealESRGAN_x4plus (general) or RealESRGAN_x4plus_anime_6B
   - Scale: 4x (128x128 → 512x512) or 2x for initial test
   - Output format: PNG (intermediate, before DDS conversion)

4. **Batch process all textures:**
   - Point input folder to `raw_assets/seyda_neen/textures/`
   - Output to `converted_assets/textures/upscaled/`

**Time per texture:** ~2-8 minutes depending on GPU
**Total time for 53 textures:** ~2-7 hours

### Option C: Hybrid Approach (Best Quality)

1. Use MET as base for common textures
2. AI upscale any textures MET doesn't cover
3. Manual touch-up in GIMP for problem areas

## Step 4.3: AI Upscaling Tips

### Avoiding Artifacts

AI upscaling can introduce artifacts. Common issues:

| Artifact | Cause | Solution |
|----------|-------|----------|
| Streaky lines | ESRGAN over-smoothing | Use RealESRGAN_x4plus_anime_6B |
| Blurry details | Low denoise strength | Increase denoise slightly |
| Color shift | Model bias | Apply color correction post-upscale |
| Tiling seams | Edge mismatch | Use tiling-aware upscaling |

### Handling Tiling Textures

Many Morrowind textures are designed to tile (repeat seamlessly).
AI upscaling can break tiling at edges.

**Solution:**
1. Before upscaling, extend the texture by 25% on each edge
2. Upscale the extended texture
3. Crop back to the center 100%
4. Or use a tiling-aware upscaler

**chaiNNer approach:**
- Use the "Tiling" option if available in the upscale model
- Or manually fix seams in GIMP after upscaling

### Color Correction

AI models often shift colors slightly. Fix in GIMP:

1. Open the upscaled texture
2. Colors > Color Balance
3. Adjust to match the original
4. Or use: Colors > Auto > Equalize

## Step 4.4: Texture Naming Convention

Name converted textures to match Starfield conventions:

```
SEY_[Category]_[Name]_[Size].dds

Examples:
SEY_Building_ImpWall01_2K.dds
SEY_Ground_BitterCoastMud_2K.dds
SEY_Furniture_Barrel01_1K.dds
```

This keeps textures organized and prevents naming conflicts.

## Step 4.5: Convert to Starfield DDS Format

### Using Texconv (Command Line)

```batch
:: Convert color textures to R8G8B8A8_UNORM_SRGB
texconv -f R8G8B8A8_UNORM_SRGB -o "converted_assets\textures" "input.png"

:: Convert to BC7 (compressed, better performance)
texconv -f BC7_UNORM_SRGB -o "converted_assets\textures" "input.png"

:: Convert normal maps to linear format
texconv -f R8G8B8A8_UNORM -o "converted_assets\textures" "normal_map.png"
```

### Using GIMP

1. Open the texture in GIMP
2. File > Export As
3. Select DDS format
4. Settings:
   - Compression: None (for testing) or BC7/DXT5 (for release)
   - Generate Mipmaps: Yes
   - Format: 32-bit RGBA
5. Export

### Batch Conversion Script

```python
#!/usr/bin/env python3
"""
batch_convert_textures.py

Batch converts upscaled PNG textures to Starfield DDS format.
Requires texconv.exe in PATH or update TEXCONV_PATH below.
"""

import os
import subprocess
import glob

TEXCONV_PATH = r"C:\Tools\texconv.exe"
INPUT_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets\textures\upscaled"
OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\converted_assets\textures"

# Find all PNG files (upscaled textures)
png_files = glob.glob(os.path.join(INPUT_DIR, "*.png"))

for png_path in png_files:
    filename = os.path.basename(png_path)
    print(f"Converting: {filename}")

    try:
        subprocess.run([
            TEXCONV_PATH,
            "-f", "R8G8B8A8_UNORM_SRGB",
            "-o", OUTPUT_DIR,
            png_path
        ], check=True)
        print(f"  OK: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: {filename} - {e}")

print("Batch conversion complete.")
```

## Step 4.6: Create Material Files (.mat)

Starfield uses .mat JSON files to define material properties.

### Basic Material Template

```json
{
  "materials": [
    {
      "name": "SEY_ImperialWall01",
      "textures": {
        "diffuse": "Materials\\Buildings\\SEY_ImperialWall01_D.dds",
        "normal": "Materials\\Buildings\\SEY_ImperialWall01_N.dds",
        "roughness": "Materials\\Buildings\\SEY_ImperialWall01_R.dds"
      },
      "properties": {
        "alpha": 1.0,
        "emissive": 0.0,
        "twoSided": false
      }
    }
  ]
}
```

**Note:** The exact .mat format may vary. Study existing Starfield materials
in the CK or extracted game files to match the format.

### Material Path Convention

```
Materials\[Category]\[Name].mat

Examples:
Materials\Buildings\SEY_ImperialWall01.mat
Materials\Ground\SEY_BitterCoastMud.mat
Materials\Furniture\SEY_Barrel01.mat
```

## Step 4.7: Landscape Texture Setup

For the ground/terrain textures, Starfield uses a biome texture system.

**Biome textures are applied based on:**
- Slope angle
- Altitude
- Distance from water

**In the CK, you'll set up:**
1. Base texture (mud for Bitter Coast)
2. Slope texture (rock for steep areas)
3. Water texture (shoreline)
4. Snow texture (if applicable)

This is configured in the Creation Kit, not through individual .mat files.

## Step 4.8: Quality Checklist (Per Texture)

- [ ] Upscaled to at least 2K (2048x2048)
- [ ] No visible AI artifacts (streaks, blurs)
- [ ] Color matches original (no major shift)
- [ ] Tiling works correctly (if applicable)
- [ ] Correct DDS format (R8G8B8A8_UNORM_SRGB for color)
- [ ] Mipmaps generated
- [ ] Named correctly (SEY_Category_Name_Size.dds)
- [ ] Material file created (.mat)
- [ ] Loads correctly in NifSkope

## Estimated Texture Count for Seyda Neen

| Category | Original Count | After Upscaling |
|----------|---------------|-----------------|
| Ground/Terrain | ~10 | ~10 |
| Imperial buildings | ~15 | ~15 |
| Dunmer buildings | ~10 | ~10 |
| Furniture | ~5 | ~5 |
| Clutter | ~5 | ~5 |
| Water | ~3 | ~3 |
| Vegetation | ~5 | ~5 |
| **Total** | **~53** | **~53** |

## Troubleshooting

**AI upscaling produces garbage:**
- Try a different model (RealESRGAN_x4plus_anime_6B for stylized art)
- Lower the denoise strength
- Try upscaling 2x first, then 2x again (multipass)

**DDS conversion fails:**
- Check input file isn't corrupted
- Ensure texconv is the latest version
- Try uncompressed format first (R8G8B8A8_UNORM_SRGB)

**Textures look blurry in-game:**
- Ensure mipmaps were generated
- Check texture resolution is at least 2K
- Verify DDS format matches Starfield expectations

**Tiling seams visible:**
- Need to fix tiling before or after upscaling
- Use GIMP's Offset filter to check tiling
- Manually blend seams in GIMP

## Checklist

- [ ] All textures identified and cataloged
- [ ] Upscaling method chosen (MET / AI / Hybrid)
- [ ] All textures upscaled to 2K+
- [ ] Color correction applied where needed
- [ ] Tiling verified for repeatable textures
- [ ] Converted to correct DDS format
- [ ] Material files created
- [ ] Named correctly
- [ ] Quality checked per texture

## Next Phase

Proceed to [Phase 5: Creation Kit Assembly](05-CREATION-KIT-ASSEMBLY.md)
to place everything in Starfield.
