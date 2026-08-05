# Phase 6: Creation Kit Cell Assembly Guide

## Overview
This guide explains how to use the generated placement data to reconstruct Seyda Neen in the Starfield Creation Kit.

## Prerequisites
- Starfield Creation Kit installed
- All converted assets in place (see below)
- 32GB+ RAM recommended

## Asset Installation
Copy the following directories into your Starfield `Data` folder:

```
Data\
  Meshes\morrowind\          <- 242 .nif files + geometries\ subdirectory
  Materials\morrowind\       <- 179 .mat files
  Textures\morrowind\         <- 179 upscaled .dds files
```

## Seyda Neen Layout

### Exterior Cells (2 cells)
Seyda Neen spans two exterior cells in Morrowind's grid system. In Starfield, these will be placed in a custom worldspace on Magnus.

| Cell | Objects | Description |
|------|---------|-------------|
| Seyda Neen (cell 0) | 278 placeable | Main exterior - lighthouse, tradehouse, docks |
| Seyda Neen (cell 1) | 183 placeable | Secondary exterior - more houses, shoreline |

### Interior Cells (13 cells)
Each building is a separate interior cell:

| Cell | Objects | Building |
|------|---------|----------|
| Arrille's Tradehouse | 178 | General store + inn |
| Census and Excise Office | 240 | Main quest start location |
| Census and Excise Warehouse | 141 | Storage basement |
| Draren Thiralas' House | 52 | Residential |
| Eldafire's House | 71 | Residential |
| Erene Llenim's Shack | 35 | Residential |
| Fargoth's House | 43 | Residential |
| Fine-Mouth's Shack | 27 | Residential |
| Foryn Gilnith's Shack | 37 | Residential |
| Indrele Rathryon's Shack | 32 | Residential |
| Lighthouse | 46 | Lighthouse interior |
| Terurise Girvayne's House | 70 | Residential |
| Vodunius Nuccius' House | 58 | Residential |

## Coordinate System
- **Morrowind units × 50 = Starfield units**
- Example: `(-10275, -71635, 260)` → `(-513750, -3581750, 13000)`
- Z is up in both systems
- Rotation is in degrees (ZYX Euler)

## Door Linking
Doors in the exterior cells have `destination` fields linking to interior cells.
The placement CSV includes the `destination_cell` column for each door reference.

Example door link:
```
ex_nord_door_01 at (-491069, -3573847, 13442)
  → "Seyda Neen, Census and Excise Office" at (1175, -610, 272)
```

## CK Workflow

### 1. Create Plugin
- Open Creation Kit
- File → New → Create new plugin: `SeydaNeen.esp`

### 2. Create Worldspace
- Create a new worldspace on Magnus (or use a test worldspace)
- Set up terrain (flat area for Seyda Neen)

### 3. Place Exterior Objects
For each row in `cell_00_Seyda_Neen.csv` and `cell_01_Seyda_Neen.csv`:
1. Open the exterior cell
2. Add object → select the converted NIF from `Meshes\morrowind\`
3. Set position (x_sf, y_sf, z_sf)
4. Set rotation (rot_x, rot_y, rot_z)
5. Assign material from `Materials\morrowind\`

### 4. Create Interior Cells
For each interior cell CSV:
1. Cell → New Interior Cell
2. Name it (e.g., "SeydaNeenArrillesTradehouse")
3. Place objects from the CSV

### 5. Set Up Door Teleportation
For each door with a `destination_cell`:
1. Select the door object
2. Add Teleport Door script
3. Set destination cell and position

## Files Reference

### Placement Data
- `converted_assets\placement\seyda_neen_all_placements.csv` - All 1491 placements
- `converted_assets\placement\cell_XX_*.csv` - Per-cell placement data
- `converted_assets\placement\placement_summary.json` - Summary statistics

### Converted Assets
- `converted_assets\meshes\` - 242 NIFs + geometries
- `Data\Materials\morrowind\` - 179 .mat files
- `converted_assets\textures_upscaled\` - 179 upscaled DDS textures

### Original Data
- `raw_assets\seyda_neen_inventory.json` - Full object inventory
- `raw_assets\seyda_neen_textures.json` - Mesh-to-texture mapping

## Notes
- 241 of 1491 placements have converted NIFs (the rest are items, containers, etc. that weren't converted)
- Focus on placing the 241 converted meshes first (buildings, terrain, flora, furniture)
- Small items (bottles, plates, etc.) can be added later
- NPCs and creatures will be handled in Phase 7
