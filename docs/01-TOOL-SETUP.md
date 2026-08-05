# Phase 1: Tool Setup & Environment Preparation

**Estimated Time:** 2-4 hours
**Prerequisites:** Morrowind GOTY Edition installed, Starfield installed

## Step 1.1: Install Starfield Creation Kit

1. Open Steam
2. Search for "Starfield Creation Kit" (free)
3. Install it
4. Launch once to verify it works (takes ~4 minutes to load)
5. Note: CK requires 32GB+ RAM minimum. Close other applications.

**First Launch Tips:**
- CK opens with all windows cluttered in the center
- Rearrange windows to your preference
- Use Docks > Save Layout to save your workspace layout
- Press 'A' to toggle light modes in the render window

**Useful CK Reference:**
- Steam Guide: "Starfield Creation Kit: An Introductory Guide for Building Outposts and POIs"
  (steamcommunity.com/sharedfiles/filedetails?id=3385012985)
- Steam Guide: "Understanding the Creation Kit" by DrNewcenstein
  (steamcommunity.com/sharedfiles/filedetails?id=3268338872)
- YouTube Playlist: "Starfield Creation Kit Basics"

## Step 1.2: Install Blender (Version 3.5 or 3.6)

**IMPORTANT:** Use Blender 3.5 or 3.6 ONLY. The Starfield Geometry Bridge plugin
is incompatible with Blender 4.0+.

1. Download Blender 3.6 LTS from blender.org
   (or archive.blender.org for older versions)
2. Install with default settings
3. Do NOT update to 4.0+ unless using NifBlend instead

**Alternative for Blender 5.0+:**
If you prefer modern Blender, use NifBlend instead of Starfield Geometry Bridge:
- GitHub: github.com/Tzeentchnet/NifBlend
- Status: Pre-alpha but functional for import
- Supports Morrowind NIF import natively
- Note: Export may have limitations vs SGB

## Step 1.3: Install Starfield Geometry Bridge (Blender Plugin)

1. Download from nexusmods.com/starfield/mods/4360
   (or GitHub: github.com/SesamePaste233/StarfieldMeshConverter)
2. Extract the release zip
3. In Blender: Edit > Preferences > Add-ons > Install
4. Select the .zip file from the release
5. Enable the addon
6. Configure in Add-on Preferences:
   - Set Starfield Data path to your Starfield installation
   - Example: `C:\Program Files (x86)\Steam\steamapps\common\Starfield\Data`

**Plugin Features:**
- Import .nif files with geometry data
- Export .nif + .mesh files for Starfield
- Handle bone rigging and morphs
- Support for LoD generation

**Discord Community:** discord.gg/TZ2Fvb7EQg

## Step 1.4: Install NifSkope (Starfield Fork)

1. Download from nexusmods.com/starfield/mods/10748
   (fo76utils fork - Starfield compatible)
2. Extract to a tools folder (e.g., `C:\Tools\NifSkope`)
3. No installation needed - just run NifSkope.exe

**用途:**
- View and edit .nif files
- Set material paths on meshes
- Verify mesh structure before export
- Check collision data

## Step 1.5: Install BAE (Bethesda Archive Extractor)

1. Download from nexusmods.com/skyrimspecialedition/mods/974
   (supports Morrowind through Starfield)
2. Extract to a tools folder
3. Run BAE.exe

**用途:**
- Extract files from Morrowind .bsa archives
- Also works with Starfield .ba2 archives
- Can browse archive contents before extracting

## Step 1.6: Install BAMgr (BA2 Manager)

1. Download from nexusmods.com/starfield/mods/14468
2. Extract to a tools folder
3. Run BAMgr.exe

**用途:**
- Create Starfield .ba2 archives
- Extract files from .ba2 archives
- Supports BA2 versions 1-3 (Starfield)
- Has "BA2 Create assistance" that auto-detects optimal settings

**Recommended:** Associate .ba2 files with BAMgr for easy access.

## Step 1.7: Install Texture Tools

### Texconv (Command Line)
1. Download from github.com/Microsoft/DirectXTex/releases
2. Extract texconv.exe to a tools folder
3. Add to your PATH or use full path in scripts

**Basic Usage:**
```batch
texconv -f R8G8B8A8_UNORM_SRGB -o "output_folder" "input_texture.dds"
```

### chaiNNer (AI Upscaling GUI)
1. Download from github.com/chaiNNer-org/chaiNNer/releases
2. Install and launch
3. Install ESRGAN models within chaiNNer:
   - RealESRGAN_x4plus (general purpose)
   - RealESRGAN_x4plus_anime_6B (for stylized textures)

### GIMP (Manual Texture Editing)
1. Download from gimp.org
2. Install DDS plugin if not included
3. Used for manual texture fixes and adjustments

## Step 1.8: Install Additional Tools

### Total Commander (Optional)
If you use Total Commander, install the BA2/BSA plugin:
- nexusmods.com/starfield/mods/6648
- Lets you browse BA2/BSA files directly in Total Commander

### ImageMagick (Optional, for batch processing)
1. Download from imagemagick.org
2. Install with legacy utilities enabled
3. Used for batch DDS conversion and manipulation

## Step 1.9: Install Required Mods

These must be installed in Starfield before testing:

1. **The Elder Star System Magnus** (v5.3+)
   - nexusmods.com/starfield/mods/12241
   - This is the base mod our city plugs into

2. **Starfield Script Extender (SFSE)**
   - sfse.silverlock.org
   - Required by many complex mods

## Step 1.10: Verify Morrowind Installation

Locate your Morrowind data files:

**Steam Default:**
```
C:\Program Files (x86)\Steam\steamapps\common\Morrowind\Data Files\
```

**Verify these BSA files exist:**
- `Morrowind.bsa` (main game)
- `Tribunal.bsa` (Tribunal expansion)
- `Bloodmoon.bsa` (Bloodmoon expansion)

**Also verify these folders exist:**
- `Meshes\` (NIF files)
- `Textures\` (DDS/TGA files)
- `Sound\` (audio files)
- `Music\` (background music)

If any are missing, verify game files through Steam:
Right-click Morrowind > Properties > Local Files > Verify integrity

## Step 1.11: Create Project Workspace

Create this folder structure (if not already done):

```
C:\Users\max\Projects\Morrowind\
├── docs\                    # This documentation
├── scripts\                 # Automation scripts
├── raw_assets\              # Extracted Morrowind files (staging)
│   ├── meshes\
│   ├── textures\
│   └── sounds\
├── converted_assets\        # Starfield-ready files
│   ├── meshes\
│   ├── textures\
│   ├── materials\
│   └── sounds\
├── reference\               # Reference images and notes
└── plugins\                 # Final ESP/ESM files
```

## Step 1.12: Create Configuration File

Create `config.ini` in the project root to store paths:

```ini
[paths]
morrowind_data = C:\Program Files (x86)\Steam\steamapps\common\Morrowind\Data Files
starfield_data = C:\Program Files (x86)\Steam\steamapps\common\Starfield\Data
blender = C:\Program Files\Blender Foundation\Blender 3.6\blender.exe
nifskope = C:\Tools\NifSkope\NifSkope.exe
bae = C:\Tools\BAE\BAE.exe
bamgr = C:\Tools\BAMgr\BAMgr.exe
texconv = C:\Tools\texconv.exe
output = C:\Users\max\Projects\Morrowind\converted_assets

[settings]
texture_upscale_factor = 4
texture_format = R8G8B8A8_UNORM_SRGB
mesh_lod_levels = 3
```

**Note:** Adjust all paths to match your actual installation locations.

## Checklist

Before proceeding to Phase 2, verify:

- [ ] Starfield Creation Kit launches successfully
- [ ] Blender 3.5/3.6 installed (NOT 4.0+)
- [ ] Starfield Geometry Bridge plugin enabled in Blender
- [ ] NifSkope (Starfield fork) can open .nif files
- [ ] BAE can open Morrowind .bsa files
- [ ] BAMgr can create .ba2 archives
- [ ] Texconv is accessible from command line
- [ ] Morrowind BSA files located and verified
- [ ] Starfield installed with Magnus mod
- [ ] Project folder structure created
- [ ] Config file created with correct paths

## Troubleshooting

**CK won't load / crashes:**
- Ensure 32GB+ RAM available
- Close all other applications
- First load takes ~4 minutes - be patient

**Blender plugin won't install:**
- Make sure you're using Blender 3.5/3.6
- Check that the .zip isn't corrupted
- Try installing from the GitHub release directly

**BAE can't open Morrowind BSA:**
- BAE should support Morrowind BSAs
- Try re-downloading BAE if version is old
- Verify BSA files aren't corrupted (reinstall Morrowind)

**NifSkope shows "Unsupported Startup Version":**
- Make sure you're using the fo76utils fork (Starfield compatible)
- The standard NifSkope may not support Morrowind NIF versions
