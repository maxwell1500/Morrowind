# Phase 2: Morrowind Asset Extraction

**Estimated Time:** 1-2 hours
**Prerequisites:** Phase 1 complete, BAE installed

## Overview

Extract all relevant Morrowind assets from BSA archives into a staging area.
We extract EVERYTHING first, then sort what we need. This is faster than
trying to pick individual files from archives.

## Step 2.1: Locate Morrowind BSA Files

**Default Steam path:**
```
C:\Program Files (x86)\Steam\steamapps\common\Morrowind\Data Files\
```

**Required BSA files:**
| File | Contents | Size |
|------|----------|------|
| `Morrowind.bsa` | Base game meshes, textures, sounds | ~300MB |
| `Tribunal.bsa` | Tribunal expansion assets | ~150MB |
| `Bloodmoon.bsa` | Bloodmoon expansion assets | ~200MB |

## Step 2.2: Extract with BAE

1. Launch BAE.exe
2. Drag `Morrowind.bsa` into the BAE window
3. Click "Extract All" or select specific folders
4. Extract to: `C:\Users\max\Projects\Morrowind\raw_assets\`
5. Repeat for `Tribunal.bsa` and `Bloodmoon.bsa`

**Important:** BAE will preserve the folder structure within the BSA.
After extraction you should see:
```
raw_assets\
├── Meshes\          # NIF 3D model files
├── Textures\        # DDS/TGA texture files
├── Sound\           # WAV/MP3 audio files
├── Music\           # Background music
└── Fonts\           # Font files
```

## Step 2.3: Understand Morrowind File Structure

### NIF Files (Meshes)
Location: `raw_assets\Meshes\`

Morrowind uses NIF version 4.0.0.2 (NiFile format 3.3).
Key naming conventions for Seyda Neen assets:

**Buildings (Imperial/Common style - used in Seyda Neen):**
- `in_c_balcony.nif` - Imperial common building parts
- `in_c_brick_wall.nif` - Imperial brick walls
- `in_c_bridge.nif` - Bridge pieces
- `in_c_dock.nif` - Dock structures
- `in_c_lighthouse.nif` - Lighthouse
- `in_c_railing.nif` - Railings
- `in_c_roof.nif` - Imperial roof pieces
- `in_c_stairs.nif` - Stair pieces
- `in_c_wall.nif` - Wall pieces
- `in_c_window.nif` - Window pieces

**Dunmer Architecture (also in Seyda Neen):**
- `in_d_*` - Dunmer interior pieces
- `ex_d_*` - Dunmer exterior pieces

**Furniture:**
- `furn_*` - Furniture items (beds, tables, chairs, shelves)
- `contain_*` - Containers (barrels, crates, sacks)

**Clutter:**
- `clutter_*` - Miscellaneous objects
- `misc_*` - Miscellaneous items

**Clothing:**
- `clothes_*` - Clothing items
- `armor_*` - Armor pieces (if needed)

### Texture Files
Location: `raw_assets\Textures\`

Morrowind textures are typically:
- 64x64 to 256x256 pixels
- DDS format (DXT1 compression for opaque, DXT5 for alpha)
- Some are TGA format

**Naming conventions:**
- `tx_bitter_coast_*` - Bitter Coast region textures
- `tx_mud_*` - Mud/ground textures
- `tx_grass_*` - Grass textures
- `tx_rock_*` - Rock textures
- `tx_imp_*` - Imperial building textures
- `tx_dun_*` - Dunmer building textures
- `tx_furn_*` - Furniture textures

## Step 2.4: Identify Seyda Neen Assets

Seyda Neen uses these asset categories:

### Must-Have Buildings

| Asset Pattern | Description | Priority |
|---------------|-------------|----------|
| `in_c_balcony*` | Imperial balconies | High |
| `in_c_brick*` | Brick walls | High |
| `in_c_dock*` | Dock structures | High |
| `in_c_lighthouse*` | The lighthouse | High |
| `in_c_railing*` | Railings | High |
| `in_c_roof*` | Imperial roofs | High |
| `in_c_stairs*` | Stairs | High |
| `in_c_wall*` | Imperial walls | High |
| `in_c_window*` | Windows | High |
| `in_d_*` | Dunmer buildings | High |

### Must-Have Textures

| Asset Pattern | Description | Priority |
|---------------|-------------|----------|
| `tx_bitter_coast_*` | Bitter Coast ground | High |
| `tx_mud_*` | Mud textures | High |
| `tx_imp_*` | Imperial building textures | High |
| `tx_dun_*` | Dunmer building textures | High |
| `tx_water*` | Water textures | High |
| `tx_grass_*` | Grass/vegetation | Medium |

### Nice-to-Have

| Asset Pattern | Description | Priority |
|---------------|-------------|----------|
| `furn_*` | Furniture | Medium |
| `clutter_*` | Clutter items | Medium |
| `clothes_*` | Clothing | Medium |
| `sound\*` | Ambient sounds | Low |
| `sound\vo\*` | Voice files | Low |

## Step 2.5: Sort Extracted Assets

After extraction, create a working copy of just what we need:

```batch
:: Create Seyda Neen-specific staging folder
mkdir "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen"

:: Copy Imperial building meshes
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Meshes\in_c_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\meshes\" /S /Y

:: Copy Dunmer building meshes
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Meshes\in_d_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\meshes\" /S /Y

:: Copy exterior building meshes
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Meshes\ex_c_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\meshes\" /S /Y
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Meshes\ex_d_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\meshes\" /S /Y

:: Copy ground/landscape textures
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Textures\tx_bitter_coast_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\textures\" /Y
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Textures\tx_mud_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\textures\" /Y
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Textures\tx_grass_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\textures\" /Y

:: Copy building textures
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Textures\tx_imp_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\textures\" /Y
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Textures\tx_dun_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\textures\" /Y

:: Copy furniture
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Meshes\furn_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\meshes\" /S /Y

:: Copy clothing
xcopy "C:\Users\max\Projects\Morrowind\raw_assets\Meshes\clothes_*" ^
      "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen\meshes\" /S /Y
```

## Step 2.6: Document What You Have

Create a manifest file listing all extracted assets:

```batch
:: Generate file listing
dir /s /b "C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen" > ^
          "C:\Users\max\Projects\Morrowind\reference\extracted_assets_list.txt"
```

Review this list to:
1. Confirm you have all needed assets
2. Note any missing assets that need alternative sourcing
3. Identify assets that can be shared across multiple cities

## Step 2.7: Cross-Reference with Reference Images

Look up Seyda Neen screenshots/walkthroughs to identify specific buildings:

**Key Seyda Neen Structures:**
1. Census and Excise Office (where you start)
2. The lighthouse
3. Arrille's Tradehouse (shop)
4. The census office dock
5. Several houses
6. The fort walls
7. The bridge

**Good reference sources:**
- uesp.net/wiki/Morrowind:Seyda_Neen
- elderscrolls.fandom.com/wiki/Seyda_Neen
- YouTube walkthroughs of Morrowind opening

Map each structure to its corresponding NIF file(s).

## Troubleshooting

**BSA extraction fails:**
- Reinstall Morrowind and verify files
- Try a different BSA extraction tool (BSA Browser, BSAPack)
- Check that BSA files aren't read-only

**Missing textures:**
- Some textures may be embedded in NIF files
- Check NIF file properties in NifSkope for texture paths
- Some textures reference external files that may be in different folders

**Too many files:**
- Morrowind has thousands of assets - we only need a fraction
- Focus on the Seyda Neen-specific assets first
- You can always extract more later

**Texture format issues:**
- Some Morrowind textures are TGA, not DDS
- Convert TGA to DDS using GIMP or Photoshop
- Some may need DXT compression applied

## Checklist

- [ ] All 3 BSA files extracted successfully
- [ ] Folder structure preserved (Meshes, Textures, Sound)
- [ ] Seyda Neen-specific assets identified and copied
- [ ] Asset manifest created
- [ ] Reference images reviewed
- [ ] Missing assets identified
- [ ] Working copy created in raw_assets/seyda_neen/

## Next Phase

Proceed to [Phase 3: Mesh Conversion](03-MESH-CONVERSION.md) to convert
Morrowind NIF files to Starfield format.
