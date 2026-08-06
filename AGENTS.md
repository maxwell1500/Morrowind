# AGENTS.md - Vvardenfell Starfield Mod

**Last Updated:** 2026-08-06
**Status:** Phase 8 — Seyda Neen visible in CK render window; terrain material fixed; harbor water set (XCLW=479.0)
**Next Steps:** Collision, doors, NPCs

---

## Project Goal

Build a Starfield mod recreating Morrowind's Vvardenfell starting with Seyda Neen, then expanding to all of Vvardenfell and eventually all of Tamriel. Add as region on Magnus's existing Nirn planet.

---

## Architecture

### Why Not Our Own Planet
- Starfield PNDT (planet data) requires PCCC (Houdini procedural terrain data) — 30KB+ binary we cannot generate
- Therefore: cannot create a real new planet
- Solution: **Override Magnus's Morrowind WRLD** on existing Nirn planet

### What We Override
- **WRLD:** Magnus's Morrowind WRLD (formID `0x0100E1C8`) — override with all 26 subrecords
- **Cells:** Magnus's existing exterior cells — override with our objects
- **Persistent cell:** Magnus's persistent cell (`0x0100E954`) — override (empty, no REFRs)

### What We Create
- **STAT records:** 241 Morrowind meshes (our formIDs `0xFE000100+`)
- **REFR records:** 434 exterior + 675 interior (our formIDs `0xFE000800+`)
- **Interior cells:** 13 cells (our formIDs `0xFE000A00+`)
- **LCTN:** Seyda Neen (`0xFE000001`), parented to Magnus's Morrowind_ID (`0x0100E774`)

### What We Reference from Magnus
- WRLD formID (`0x0100E1C8`)
- Cell formIDs (442 exterior cells at various grid coordinates)
- Persistent cell formID (`0x0100E954`)
- Morrowind_ID LCTN formID (`0x0100E774`)
- SNAM, PNAM, BNAM, XLCN, CNAM subrecord values

---

## Coordinate System — CRITICAL

### The Scale Bug (discovered 2026-07-02)
Morrowind uses **8192-unit cells**. Magnus's WRLD uses **100-unit cells** (set via DNAM subrecord `(200.0, 160.0)`).

**Scale factor: `100 / 8192 ≈ 0.0122`**

Without scaling, a village that should fit in 1 cell spans 76 × 160 cells.

### Coordinate Pipeline
```
Morrowind world coords (x_mw, y_mw, z_mw)
  → Scale: x = x_mw * (100/8192), y = y_mw * (100/8192), z = z_mw * (100/8192)
  → Offset: x += OFFSET_X, y += OFFSET_Y, z += Z_OFFSET
  → Write to REFR DATA subrecord as (x, y, z, rx, ry, rz) — 6 floats, 24 bytes
```

### Current Offsets (VERIFIED 2026-08-06 from deployed ESP)
- `SCALE = 100.0 / 8192.0`
- `OFFSET_X = 92.6` (verified: ex_nord_door_01 x_mw=-9821.382 → -27.29 matches deployed REFR)
- `OFFSET_Y = 802.0`
- `Z_OFFSET = 480.0`
- NOTE: The old -1900/-1169/480 offsets below are STALE (match generate_btd.py v1-3, not the deployed ESP)
- NOTE: Deployed ESP z uses a local-z source (≈480 + z_local×SCALE, z_local ∈ -26..23); the current placement CSV stores absolute z_mw (268–452). The golden ESP's exact generator is lost; the current `generate_full_seydaneen.py` (7/24) DOES NOT reproduce it (see STATUS.md "Known generator regression"). Treat deployed/committed `SeydaNeen.esp` as golden.

### Cell Grid Computation
- **File format:** XCLC uses 4096-unit cell grid (standard Bethesda)
- **CK display:** Shows 100-unit cells (from WRLD DNAM)
- Conversion: display_cell = file_cell * (4096/100) = file_cell * 40.96
- Example: file cell (-1,-1) → CK display cell (-41,-41)

### CK Coordinate Display
CK shows coordinates in the Cell View differently from the Edit Properties window:
- **Edit Properties:** Shows absolute world coordinates (X, Y, Z)
- **Cell View:** May display coordinates in a different order or relative to cell origin

---

## Magnus.esm Structure

### File Format
- **No 2-byte alignment** between top-level records (unlike older Bethesda games)
- GRUP type at offset +12 (not +16)
- Record formID at offset +12, flags at +8, version at +16

### WRLD Records Found
| FormID | Type | Notes |
|--------|------|-------|
| `0x00208D92` | Override of Starfield.esm | Nirn planet surface WRLD |
| `0x0100E1C8` | Magnus's own | **Morrowind WRLD** — what we override |
| `0x010160C8` | Magnus's own | Another worldspace |
| `0x0101EE3E` | Magnus's own | Another worldspace |
| `0x0102D54E` | Magnus's own | Another worldspace |
| `0x01033CE0` | Magnus's own | Another worldspace |
| `0x0103A102` | Magnus's own | Another worldspace |
| `0x01042CD8` | Magnus's own | Another worldspace |

### Cell Coverage
- **442 exterior cells** total
- Grid X range: -41 to 18 (60 unique X coords)
- Grid Y range: -17 to 26 (44 unique Y coords)
- Not all grid coordinates exist — only 442 out of ~2640 possible cells
- Cells are named "Surface" (Magnus's naming convention)

### Key Cell FormIDs
| Grid | FormID | Notes |
|------|--------|-------|
| (-1,-1) | `0x010478A1` | **Our cell** — Seyda Neen placed here |
| (-2,-10) | `0x010488FA` | Original test cell |
| (-2,-9) | `0x01047C5B` | Original test cell |
| (-10,0) | `0x0100E852` | Used by ImperialCity.esm |
| (-10,-1) | `0x0100E6F4` | Used by ImperialCity.esm |
| Persistent | `0x0100E954` | Must always override |

### Magnus.esm Masters
- Only 1 master: `Starfield.esm`
- Magnus.esm is a master file (ESM), not a plugin (ESP)
- Its formIDs use file index 0x01 (e.g., `0x0100E1C8`)

---

## ESP Binary Format

### TES4 Header (24 bytes)
```
Offset  Size  Field
0       4     Signature ("TES4")
4       4     Data size (total - 24)
8       4     Flags (0x00000101 = ESL+ESM)
12      4     FormID (0x00000000)
16      4     Version (0x00000000)
20      4     Unknown (0x00000240)
```

### Record Header (24 bytes)
```
Offset  Size  Field
0       4     Signature
4       4     Data size (total - 24)
8       4     Flags
12      4     FormID
16      4     Version (0x00000000)
20      4     Unknown (0x00000240)
```

### GRUP Header (24 bytes)
```
Offset  Size  Field
0       4     Signature ("GRUP")
4       4     Total size (including 24-byte header)
8       4     Label (4 bytes — formID, string, or int16 pair)
12      4     Group type
16      8     Padding (zeros)
```

### Group Types
| Type | Name | Label |
|------|------|-------|
| 0 | Top-level | Record type string (e.g., "STAT", "WRLD", "CELL") |
| 1 | WRLD children | WRLD formID |
| 2 | Interior cell block | 0 (unused) |
| 3 | Interior cell subblock | Subblock index |
| 4 | Exterior cell block | `(block_y, block_x)` as int16 pair |
| 5 | Exterior cell subblock | `(sub_y, sub_x)` as int16 pair |
| 6 | Cell children | Cell formID |
| 8 | Persistent children | Cell formID |
| 9 | Temporary children | Cell formID |

### WRLD Override Structure
```
GRUP type=0 (label="WRLD")
  WRLD record (flags=0x00000004 for override)
  GRUP type=1 (label=WRLD_formID)
    CELL record (persistent, compressed)
    GRUP type=6 (label=persistent_cell_fid)
      GRUP type=8 (label=persistent_cell_fid) [empty]
    GRUP type=4 (label=block_coords)
      GRUP type=5 (label=subblock_coords)
        CELL record (exterior)
        GRUP type=6 (label=cell_fid)
          GRUP type=9 (label=cell_fid) [REFRs]
```

### WRLD Subrecords (26 total)
```
EDID, BFCB, SNAM, PNAM, BNAM, BFCE, FULL, XLCN, CNAM,
NAM2, NAM7, NAM3, NAM4, DNAM, MNAM, ONAM, NAMA, DATA,
FNAM, NAM0, NAM9, GNAM, XCLW, WHGT, HNAM
```

### STAT Record Subrecords
```
EDID: editor ID (null-terminated string)
OBND: object bounds (6 floats, -1/-1/-1 to 1/1/1)
ODTY: object type (uint32, 0=static)
BFCB: keyword form component (string "BGSKeywordForm_Component")
BFCE: keyword form (empty)
MODL: model path (null-terminated, e.g., "morrowind\\ex_nord_house_03.nif")
FLLD: flags (uint32, 1=static)
DNAM: two floats (1.0, 1.0)
```

### Exterior Cell Subrecords
```
DATA: 0x00000202 (exterior + use water data) — CRITICAL: must match Magnus's original
XCLC: grid_x, grid_y, flags (3 int32)
LTMP: lighting template (uint32, 0)
XCLW: water height (float, FLT_MAX = 3.4028234663852886e+38 for no water)
XILS: image space lighting (float, 1.0)
```

### REFR DATA Subrecord
- 24 bytes: 6 floats (x, y, z, rx, ry, rz)
- Rotations in radians (degrees × π/180)
- Position is absolute world coordinates

### Compressed Records
- Set flag `0x00040000` on record flags
- Data: 4-byte uncompressed size + zlib compressed data
- Used for: persistent CELL, interior CELLs

### FormID Allocation
```
0xFE000001  LCTN (Seyda Neen)
0xFE000100+ STAT records (241 total)
0xFE000800+ REFR records (1109 total)
0xFE000A00+ Interior CELL records (13 total)
```

---

## NIF Conversion

### Pipeline
1. **Import:** `bpy.ops.import_scene.mw(filepath=nif_path)` — Morrowind NIF import addon
2. **Cleanup:** Delete collision objects, ensure UV maps
3. **Export:** `bpy.ops.export_scene.custom_nif(...)` — SGB (Starfield Geometry Bridge) addon

### Critical Export Settings
```python
bpy.ops.export_scene.custom_nif(
    filepath=nif_output,
    use_internal_geom_data=True,     # Embed geometry in NIF (not external .mesh)
    export_material=False,            # Don't export .mat files (broken for Morrowind NIFs)
    export_sf_mesh_hash_result=False,# Use original filenames, not hashed
    export_template='Auto'           # Auto-select template based on root name
)
```

### NIF Material Paths — UNRESOLVED
The SGB `EditNifBSGeometries` and `CreateNifFromJson` functions crash on NIFs with multiple geometries (C++ exception `0xe06d7363`). This is a bug in `MeshConverter.dll`.

**Current state:** NIFs have geometry and `BSLightingShaderProperty` but no material path. CK shows purple boxes (missing material).

**Failed approaches:**
- `EditNifBSGeometries` with `overwrite_material_paths=True/False` — crashes
- `CreateNifFromJson` — crashes
- Binary patching (replacing `MATERIAL_PATH` placeholder) — corrupts NIFs (shifts byte offsets)
- Blender additive export — fails (no root object found)

**Potential solutions:**
- Use NifSkope to batch-edit material paths
- Write a proper NIF parser that handles offset correction
- Set material path in Blender before export (requires proper material setup)

### NIF Format
- Starfield uses `Gamebryo File Format, Version 20.2.0.7` (same as our converted NIFs)
- Material path stored as a string after `MaterialID` node name
- Example from Starborn bed: `"Materials\Ships\Starborn\StarbornShipIntFabricPanel01.mat"`

---

## Texture Pipeline

### Conversion
1. Extract DDS from BSA (BAE)
2. Convert to BC3 (texconv) — original Morrowind format
3. Upscale 2x (RealESRGAN)
4. Convert to BC7 (texconv) — Starfield format

### Material Files
- 179 `.mat` files in `Data\Materials\morrowind\`
- Each references a BC7 DDS texture
- Material path pattern: `Data\Materials\morrowind\{texture_name}.mat`

### Texture Sizes
- Our upscaled: avg 129KB, max 0.7MB, total 22.6MB
- Native Starfield: avg 1.57MB, max 21.3MB, total 0.9GB
- Our textures are **much smaller** than native — no size issue

---

## ImperialCity.esm Analysis

### Structure (73,950 bytes, 829 records)
```
[138-6717]   GRUP type=0 label='ARMO' (armor group)
[6717-7238]  CONT record
[7238-9019]  GRUP type=0 label='DOOR' (door group)
[9019-22981] 64 STAT records (standalone, NOT in a group)
[22981-23376] GRUP type=0 label='NPC_' (NPC group)
[23376-25512] GRUP type=2 (INTERIOR CELL group)
[25512-25878] WRLD 0x0100E1C8 (first override)
[25878-26496] GRUP type=1 (WRLD children — persistent cell only)
[26496-26932] WRLD 0x010160C8 (second WRLD — different worldspace)
[26932-66947] GRUP type=1 (WRLD children — 289 REFRs in other worldspace)
```

### Key Differences from Our Approach
- ImperialCity has **TWO** WRLD records: Morrowind (0x0100E1C8) and another (0x010160C8)
- The 289 REFRs are in the **other worldspace**, NOT in Morrowind
- Morrowind WRLD only has 2 REFRs (persistent cell + 1 exterior cell)
- STAT records are at top level (not in a GRUP)
- Interior CELL group comes BEFORE WRLD group

---

## Key Bug Fixes (2026-07-02)

### 1. CELL DATA = 0x00000202
Must match Magnus's original. Bit 9 (0x200) = "use water data". Without it, CK may not render cell contents.

### 2. XCLW = FLT_MAX
Water height must be `3.4028234663852886e+38` (FLT_MAX), not `0.0`. Setting to 0.0 creates a water plane at z=0 that covers everything.

### 3. Coordinate Scaling
Morrowind uses 8192-unit cells, Magnus uses 100-unit cells. Must scale by `100/8192`.

### 4. No 2-byte Alignment
Starfield ESMs don't pad records to even offsets. Adding padding breaks parsing.

### 5. GRUP Type at +12
GRUP type is at offset +12 from GRUP start, not +16.

### 6. Record Fields
FormID at +12, flags at +8, version at +16 (not the other way around).

### 7. Interior Cells Before WRLD
Interior CELL group must come before WRLD group in file order (matching ImperialCity.esm).

### 8. FormID Collision
LCTN and first STAT must not share formID. LCTN at `0xFE000001`, STATs start at `0xFE000100`.

---

## File Structure

```
C:\Users\max\Projects\Morrowind\
├── AGENTS.md                          # This file
├── config.ini                         # Tool paths
├── docs\                              # Documentation
├── raw_assets\                        # Original Morrowind assets
│   ├── Morrowind_Full\                # Extracted BSA contents
│   │   ├── meshes\                    # Original NIFs
│   │   └── textures\                   # Original DDS
│   └── seyda_neen_inventory.json      # Asset inventory
├── converted_assets\                  # Converted assets
│   ├── meshes\                        # 242 Starfield NIFs
│   ├── textures\                      # 179 BC3 DDS
│   ├── textures_upscaled\             # 179 upscaled BC7 DDS
│   ├── placement\                     # 15 cell CSVs + combined
│   │   ├── seyda_neen_all_placements.csv  # 1,491 placements
│   │   └── placement_summary.json
│   └── mapping\                       # Asset mapping CSVs
│       ├── seyda_neen_asset_mapping.csv
│       └── texture_map.json
├── Data\                              # Deployed to Starfield
│   ├── Materials\morrowind\           # 179 .mat files (+ fixed temp_terrain_color.mat)
│   ├── SeydaNeen.esp                  # Generated ESP (golden 120,181 B)
│   ├── meshes\morrowind\              # 242 NIFs + seyda_neen_terrain.nif
│   ├── Textures\morrowind\            # terrain color DDS
│   └── Terrain\Morrowind\             # BTD files
├── scripts\                           # Automation
│   ├── batch_convert_meshes.py        # Blender NIF conversion
│   ├── batch_convert_textures.py      # DDS conversion + upscale
│   ├── generate_materials.py          # .mat file generation + NIF patching
│   ├── generate_full_seydaneen.py     # MAIN ESP generator
│   ├── generate_test_vanilla.py       # Simple test ESP (1 object)
│   └── ...
└── tools\                             # Installed tools
    ├── blender-3.6\                   # Blender 3.6.13
    ├── SGB\tool_export_mesh\          # Starfield Geometry Bridge
    │   ├── MeshConverter.dll          # C++ DLL (has bugs with multi-geometry NIFs)
    │   ├── NifIO.py                   # NIF import/export
    │   └── ...
    └── ...
```

---

## Scripts Reference

### `generate_full_seydaneen.py` — Main ESP Generator
- Reads `seyda_neen_all_placements.csv` for object placements
- Reads `seyda_neen_asset_mapping.csv` for NIF paths
- Generates `SeydaNeen.esp` with:
  - 241 STAT records
  - 434 exterior REFRs in 1 cell (-1,-1)
  - 13 interior cells with 675 REFRs
  - WRLD override (0x0100E1C8)
  - Persistent cell override
  - Seyda Neen LCTN
- **Key constants:**
  - `SCALE = 100.0 / 8192.0`
  - `OFFSET_X = -1900.0`
  - `OFFSET_Y = -1169.0`
  - `Z_OFFSET = 480.0`

### `batch_convert_meshes.py` — NIF Conversion
- Run: `blender --background --python scripts/batch_convert_meshes.py`
- Converts 242 Morrowind NIFs to Starfield format
- Uses SGB addon (`tool_export_mesh`)
- Output: `converted_assets\meshes\*.nif`

### `batch_convert_textures.py` — Texture Conversion
- Converts DDS to BC3, upscales 2x with RealESRGAN, converts to BC7
- Output: `converted_assets\textures\` and `textures_upscaled\`

### `generate_materials.py` — Material Generation
- Creates 179 `.mat` files from texture mapping
- Attempts to patch NIF material paths (mostly fails due to DLL bug)

---

## Testing Workflow

### CK Launch
- Use **CK High Priority** desktop shortcut only
- CK crash dumps: `C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.*.dmp`
- CK errors: `C:\XboxGames\Starfield\Content\EditorWarnings.txt` (cumulative)

### Loading ESP
1. Launch CK via High Priority shortcut
2. File → Data → select `SeydaNeen.esp`, check "Active", OK
3. Wait for load (may take a minute with 1109 REFRs)

### Navigating to Objects
1. Cell View window → Worldspace dropdown → select "Morrowind"
2. Find "Surface" cell at grid (-1,-1) — double-click
3. In render window, double-click objects in Cell View reference list to focus

### COW Command (in-game)
- `cow 0200E1C8 -2050 -2070` (formID remapped for load order)

---

## Open Issues

### Terrain Material (RESOLVED 2026-08-06)
- `temp_terrain_color.mat` had a CDB ID collision with `tx_bc_bank.mat` (identical `res:` component IDs — copied template, never re-randomized)
- Engine reported "Material Materials\\morrowind\\temp_terrain_color.mat can't be loaded" (EditorWarnings 7/12)
- Fix: regenerated unique 16-hex component IDs (kept valid class suffix `:BAF4C608:4D584B55`), verified 4 distinct IDs × 2 pairings, zero overlap with tx_bc_bank
- Terrain mesh: `seyda_neen_terrain.nif` (500×500, z 475.7–486.2) at REFR (-357.40, -348.00, 475.75) — covers town cluster

### Terrain = Static Mesh, Not LAND
- Deployed ESP carries terrain as STAT `seyda_neen_terrain` (0xFE0001F1) + 1 REFR (0xFE000647), NOT LAND records
- Deployed `Terrain\Morrowind\Morrowind.btd` is a 64-byte stub (header-only) — CK generated flat 480.0 `.btc` caches from it
- `generate_btd_v4.py` has a bbox bug (clamped to first land cell) — FIXED 2026-08-06 but needs re-run + CK cache regen

### Generator Regression (2026-08-06)
- Current `generate_full_seydaneen.py` (7/24) does NOT reproduce the deployed/golden ESP:
  offsets 5986/51539 vs 92.6/802, 12 cells vs 1 cell, XCLW=0.0 vs FLT_MAX, WRLD-before-CELL vs CELL-before-WRLD, REFR flags 0x10400 vs 0x0
- `generate_esp_vvardenfell.py` also fails to reproduce Vvardenfell.esp
- The deployed ESP's exact generator is lost (z source differs from current CSV)

### "Wrong Cell for Its Location" Warnings
- 439 warnings in EditorWarnings.txt
- AGENTS.md previously noted as "cosmetic, doesn't prevent loading"
- Objects DO load and are visible despite warnings
- May be caused by GRUP hierarchy mismatch (type=4 vs type=5)

### "Wrong Cell for Its Location" Warnings
- 439 warnings in EditorWarnings.txt
- AGENTS.md previously noted as "cosmetic, doesn't prevent loading"
- Objects DO load and are visible despite warnings
- May be caused by GRUP hierarchy mismatch (type=4 vs type=5)

### Interior Cell Warnings
- "Improperly positioned interior cell" — 13 warnings
- "Potentially Invalid X/Y value" — interior REFR coordinates flagged
- Interior cells use local coordinates (positive values) which CK flags as invalid for exterior

### Missing Features
- NPCs/creatures
- Landscape textures
- Door teleportation (interior ↔ exterior links)
- Water/LOD
- Collision

---

## Future Phases

### Phase 9: Full Vvardenfell
- Scale from Seyda Neen to entire Vvardenfell island
- Need to map all Morrowind cells to Magnus's coordinate system
- Scale factor: `100/8192` for coordinates, find Magnus cells for each area

### Phase 10: All Tamriel
- Expand to entire continent
- May need additional WRLD overrides or LCTN hierarchy

### Long-term
- NPCs with AI packages
- Quests
- Creatures
- Landscape texturing
- Water systems
- LOD generation

---

## Contacts & Resources

- **Magnus Mod:** RONALDMCDONLD (Nexus Mods)
- **xEdit:** https://github.com/evilk/loot/releases
- **SGB:** Greatness7's Starfield Geometry Bridge
- **CK High Priority launcher:** `LaunchCK_HighPriority.ps1` + desktop shortcut
- **Blender 3.6:** `C:\Users\max\Projects\Morrowind\tools\blender-3.6\blender-3.6.13-windows-x64\blender.exe`
- **NifSkope:** `C:\Users\max\Projects\Morrowind\tools\nifskope\NifSkope\NifSkope.exe`
- **Texconv:** `C:\Users\max\AppData\Local\Microsoft\WinGet\Links\texconv.exe`
