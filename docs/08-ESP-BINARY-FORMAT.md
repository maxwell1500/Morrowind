# 08-ESP-BINARY-FORMAT.md

**Last Updated:** 2026-07-02
**Status:** Active — Full ESP format cracked; Seyda Neen visible in CK render window.

---

## Summary

This document captures the byte-level structure of a Starfield ESP file as discovered while building `SeydaNeen.esp`. It is intended as a reference for scaling the generator to the full town and for future Morrowind city conversions.

**Critical fix that made CK read the file:** the `TES4` record header must be **24 bytes**, not 20. A 20-byte header shifted every subsequent record by 4 bytes.

---

## TES4 Header (24 bytes)

| Offset | Size | Field | Notes |
|--------|------|-------|-------|
| 0x00 | 4 | Signature | `TES4` |
| 0x04 | 4 | Data Size | Size of subrecord data after the 24-byte header |
| 0x08 | 4 | Flags | `0x00000101` for ESL+ESM (light master) |
| 0x0C | 4 | FormID | `0x00000000` for TES4 |
| 0x10 | 4 | Version | `0x00000000` |
| 0x14 | 4 | Unknown | `0x00000240` |

### TES4 Subrecords

| Subrecord | Size | Purpose |
|-----------|------|---------|
| `HEDR` | 12 | Version (float), record count (uint32), next formID (uint32) |
| `CNAM` | variable | Author name, null-terminated |
| `BNAM` | variable | Plugin category (`Main`) |
| `INCC` | 4 | Internal version |
| `MAST` | variable | Master filename, null-terminated |
| `DATA` | 8 | Master file size (uint64, 0 for our ESP) |

Our ESP declares these masters:
- `Starfield.esm`
- `The Elder Star System - Magnus.esm`

---

## Record Header (24 bytes)

| Offset | Size | Field | Notes |
|--------|------|-------|-------|
| 0x00 | 4 | Signature | `CELL`, `REFR`, `STAT`, `WRLD`, `LCTN`, etc. |
| 0x04 | 4 | Data Size | Size of data after this 24-byte header |
| 0x08 | 4 | Flags | Compressed: `0x00040000`. Override: `0x00000004`. |
| 0x0C | 4 | FormID | Plugin-local formID |
| 0x10 | 4 | Version | `0x00000000` |
| 0x14 | 4 | Unknown | `0x00000240` |

---

## GRUP Header (24 bytes)

| Offset | Size | Field | Notes |
|--------|------|-------|-------|
| 0x00 | 4 | Signature | `GRUP` |
| 0x04 | 4 | Size | Total GRUP size **including** this 24-byte header |
| 0x08 | 4 | Label | Type-0: 4-byte ASCII record type. Type 4/5: int16 pair. Type 6/8/9: cell formID. |
| 0x0C | 4 | Type | See Group Types table |
| 0x10 | 8 | Padding | Zeroes |

Content length = `size - 24`.

### Group Types

| Type | Name | Label |
|------|------|-------|
| 0 | Top-level | Record type string (e.g., `STAT`, `WRLD`, `CELL`) |
| 1 | WRLD children | WRLD formID |
| 2 | Interior cell block | 0 (unused) |
| 3 | Interior cell subblock | Subblock index |
| 4 | Exterior cell block | `(block_y, block_x)` as signed int16 pair |
| 5 | Exterior cell subblock | `(sub_y, sub_x)` as signed int16 pair |
| 6 | Cell children | Cell formID |
| 8 | Persistent children | Cell formID |
| 9 | Temporary children | Cell formID |

---

## WRLD Override Structure

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

Key values from ImperialCity.esm:
- `DNAM`: `(200.0, 160.0)` — defines cell size as 100 units
- `DATA`: `0x01`
- `FNAM`: `0x18`
- `NAM0`: `(-4100.0, -1000.0)` — terrain LOD bounds
- `NAM9`: `(200.0, 2400.0)` — terrain LOD bounds

---

## Compressed Records

When the compressed flag (`0x00040000`) is set, the record data section is:

```
[4 bytes: uncompressed size (little-endian)]
[N bytes: zlib-compressed subrecords]
```

Used for: persistent CELL, interior CELLs.

---

## Subrecord Format

| Field | Size |
|-------|------|
| Signature | 4 bytes ASCII |
| Size | 2 bytes little-endian |
| Data | Size bytes |

### STAT Subrecords

| Subrecord | Data | Notes |
|-----------|------|-------|
| `EDID` | null-terminated string | Editor ID |
| `OBND` | 6 floats | Object bounds (-1/-1/-1 to 1/1/1) |
| `ODTY` | uint32 | Object type (0=static) |
| `BFCB` | string | `"BGSKeywordForm_Component\0"` |
| `BFCE` | empty | Keyword form |
| `MODL` | null-terminated string | Model path, e.g. `morrowind\ex_nord_house_03.nif` |
| `FLLD` | uint32 | Flags (1=static) |
| `DNAM` | 2 floats | (1.0, 1.0) |

### Exterior CELL Subrecords

| Subrecord | Data | Notes |
|-----------|------|-------|
| `DATA` | uint32 | `0x00000202` (exterior + use water data) — **must match Magnus's original** |
| `XCLC` | 3 × int32 | Grid (x, y, flags) |
| `LTMP` | uint32 | Lighting template (0) |
| `XCLW` | float | Water height — **FLT_MAX** (3.4028234663852886e+38) for no water |
| `XILS` | float | Image space lighting (1.0) |

### Interior CELL Subrecords

| Subrecord | Data | Notes |
|-----------|------|-------|
| `EDID` | null-terminated string | Editor ID |
| `FULL` | null-terminated string | Display name |
| `DATA` | uint32 | `0x00010025` (interior + public + has image space) |

### REFR Subrecords

| Subrecord | Data | Notes |
|-----------|------|-------|
| `NAME` | uint32 | Base object formID (STAT, DOOR, etc.) |
| `DATA` | 6 × float | Position (x, y, z) + Rotation (rx, ry, rz) in radians |

### LCTN Subrecords

| Subrecord | Data | Notes |
|-----------|------|-------|
| `EDID` | null-terminated string | Editor ID |
| `FULL` | null-terminated string | Display name |
| `PNAM` | uint32 | Parent LCTN formID |

---

## FormID Allocation

```
0xFE000001  LCTN (Seyda Neen)
0xFE000100+ STAT records (241 total)
0xFE000800+ REFR records (1109 total)
0xFE000A00+ Interior CELL records (13 total)
```

---

## Block / Sub-block Label Calculation

For a CELL at grid `(X, Y)` with cell size 4096:

- **Block label:** `struct.pack("<hh", block_y, block_x)` where `block_x = X // 32`, `block_y = Y // 32`
- **Sub-block label:** `struct.pack("<hh", sub_y, sub_x)` where `sub_x = X // 8`, `sub_y = Y // 8`
- Use Python floor division (`//`), not truncation toward zero

---

## Coordinate System

### The Scale Bug (discovered 2026-07-02)

Morrowind uses **8192-unit cells**. Magnus's WRLD uses **100-unit cells** (set via DNAM subrecord `(200.0, 160.0)`).

**Scale factor: `100 / 8192 ≈ 0.0122`**

### Coordinate Pipeline

```
Morrowind world coords (x_mw, y_mw, z_mw)
  → Scale: x = x_mw * (100/8192), y = y_mw * (100/8192), z = z_mw * (100/8192)
  → Offset: x += OFFSET_X, y += OFFSET_Y, z += Z_OFFSET
  → Write to REFR DATA subrecord as (x, y, z, rx, ry, rz) — 6 floats, 24 bytes
```

### Current Offsets

- `SCALE = 100.0 / 8192.0`
- `OFFSET_X = -1900.0` (centers Seyda Neen in Magnus cell (-1,-1))
- `OFFSET_Y = -1169.0`
- `Z_OFFSET = 480.0` (raises above Magnus's terrain at z~490)

### Cell Grid Computation

- **File format:** XCLC uses 4096-unit cell grid (standard Bethesda)
- **CK display:** Shows 100-unit cells (from WRLD DNAM)
- Conversion: `display_cell = file_cell * (4096/100) = file_cell * 40.96`
- Example: file cell (-1,-1) → CK display cell (-41,-41)

---

## Magnus.esm Structure

### File Format Quirks

- **No 2-byte alignment** between top-level records (unlike older Bethesda games)
- GRUP type at offset **+12** (not +16)
- Record formID at offset **+12**, flags at **+8**, version at **+16**

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

---

## ImperialCity.esm Structure (Reference)

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

Key differences from our approach:
- ImperialCity has **TWO** WRLD records: Morrowind (0x0100E1C8) and another (0x010160C8)
- The 289 REFRs are in the **other worldspace**, NOT in Morrowind
- Morrowind WRLD only has 2 REFRs (persistent cell + 1 exterior cell)
- STAT records are at top level (not in a GRUP)
- Interior CELL group comes **BEFORE** WRLD group

---

## Key Bug Fixes (2026-07-02)

1. **CELL DATA = 0x00000202** — Must match Magnus's original. Bit 9 (0x200) = "use water data".
2. **XCLW = FLT_MAX** — Water height must be `3.4028234663852886e+38`, not `0.0`.
3. **Coordinate Scaling** — Morrowind uses 8192-unit cells, Magnus uses 100-unit cells. Scale by `100/8192`.
4. **No 2-byte Alignment** — Starfield ESMs don't pad records to even offsets.
5. **GRUP Type at +12** — GRUP type is at offset +12 from GRUP start, not +16.
6. **Record Fields** — FormID at +12, flags at +8, version at +16.
7. **Interior Cells Before WRLD** — Interior CELL group must come before WRLD group.
8. **FormID Collision** — LCTN and first STAT must not share formID.

---

## Remaining Unknowns

1. **NIF material paths** — SGB `EditNifBSGeometries` crashes on multi-geometry NIFs. Need alternative.
2. **Door teleportation** — How to encode destination cell + position in Starfield.
3. **NPCs/creatures** — Record format for NPC_ and CREA records.
4. **Landscape texturing** — How to apply terrain textures to Magnus's terrain.
5. **Water/LOD** — Water systems and LOD generation for our cells.

---

## Tools Used

- **xEdit 4.1.5f** (`xSFEdit64.exe`) — read ESP and report parse errors
- **Creation Kit** — secondary verification
- **Python scripts:**
  - `scripts\generate_full_seydaneen.py` — main ESP generator
  - `scripts\generate_test_vanilla.py` — simple test ESP
  - `scripts\parse_imperialcity.py` — reference mod parser
  - `scripts\analyze_magnus.py` — Magnus ESM structure
