# Morrowind in Starfield - Seyda Neen Project

**Goal:** Recreate Morrowind's starting town Seyda Neen inside Starfield, using actual Morrowind assets converted to Starfield's format, as a companion mod to The Elder Star System Magnus.

## Current Status (2026-07-03)

**Textures rendering in CK!** All 241 objects show Morrowind textures. Complete pipeline working:

1. Morrowind NIF → Blender → SGB → Starfield NIF (with material paths)
2. .mat files cloned from Starborn template (valid CDB resource IDs)
3. Original Morrowind DDS textures deployed to `Data\Textures\morrowind\`

## Project Structure

```
Morrowind/
├── README.md                          # This file
├── STATUS.md                          # Current project status
├── AGENTS.md                          # AI agent instructions
├── TESTING_INSTRUCTIONS.md            # How to test in-game
├── docs/
│   ├── 00-PLAN-OVERVIEW.md            # High-level project plan
│   ├── 01-TOOL-SETUP.md               # Software installation
│   ├── 02-ASSET-EXTRACTION.md         # Extracting Morrowind BSA files
│   ├── 03-MESH-CONVERSION.md          # NIF to Starfield mesh pipeline
│   ├── 04-TEXTURE-CONVERSION.md       # Texture conversion
│   ├── 05-CREATION-KIT-ASSEMBLY.md    # Building the cell in CK
│   ├── 06-NPCS-CREATURES.md           # NPCs, dialogue, creatures
│   ├── 07-PACKAGING-TESTING.md        # BA2 packaging, testing
│   ├── MAGNUS-INTEGRATION.md          # How this mod integrates with Magnus
│   ├── CITY-TEMPLATE.md               # Reusable template for future cities
│   └── LESSONS-LEARNED.md             # Running log of discoveries
├── scripts/                           # Automation scripts
│   ├── batch_convert_meshes.py        # NIF conversion (Blender headless)
│   ├── batch_convert_textures.py      # DDS conversion + upscale
│   ├── generate_materials.py          # .mat file generation
│   ├── generate_full_seydaneen.py     # Main ESP generator
│   └── ...
├── raw_assets/                        # Original Morrowind assets
│   ├── Morrowind_Full/                # Extracted BSA contents
│   │   ├── meshes\                    # Original NIFs
│   │   └── textures\                   # Original DDS
│   └── seyda_neen_inventory.json      # Asset inventory
├── converted_assets/                  # Converted assets
│   ├── meshes\                        # 242 Starfield NIFs
│   ├── textures\                      # 179 BC3 DDS
│   ├── textures_upscaled\             # 179 upscaled BC7 DDS
│   ├── placement\                     # 15 cell CSVs + combined
│   └── mapping\                       # Asset mapping CSVs
├── Data\                              # Deployed to Starfield
│   ├── Materials\morrowind\           # 238 .mat files
│   ├── SeydaNeen.esp                  # Generated ESP
│   └── meshes\morrowind\              # 242 NIFs
└── tools\                             # Installed tools
    ├── blender-3.6\                   # Blender 3.6.13
    ├── SGB\tool_export_mesh\          # Starfield Geometry Bridge
    └── ...
```

## Key References

| Resource | URL |
|----------|-----|
| Elder Star System Magnus | nexusmods.com/starfield/mods/12241 |
| Imperial City of Cyrodiil | nexusmods.com/starfield/mods/15999 |
| Starfield Geometry Bridge | nexusmods.com/starfield/mods/4360 |
| BAE (Archive Extractor) | nexusmods.com/skyrimspecialedition/mods/974 |
| NifSkope (Starfield) | nexusmods.com/starfield/mods/10748 |

## How This Fits With Magnus

The Elder Star System Magnus creates planet Nirn with provinces as biomes.
Each province has its own landing area. Seyda Neen is located in the
Morrowind province (Vvardenfell). Our mod overrides Magnus's Morrowind WRLD
and places converted Morrowind objects in the existing cell grid.

## Adapted From

This project follows conversion techniques proven by the Imperial City of
Cyrodiil mod, which converted Rigmor of Cyrodil assets to Starfield format
over 137+ hours of work.
