# Vvardenfell Mod — Status (2026-08-06)

## Water (added 2026-08-06)

- **Exterior cell (-1,-1) `0x010478A1`: XCLW = 479.0** (water plane)
- Persistent cell `0x0100E954`: XCLW = FLT_MAX (no water) — verified by decompressing the compressed record
- Interior cells: no XCLW (no exterior water; interiors use their own mechanism)
- Water level rationale (from deployed geometry):
  - All 435 exterior REFRs sit at z ≥ 479.22; terrain mesh is the only object lower (475.75)
  - Dock deck under the harbor: z 478.07–479.08 → submerged (harbor water)
  - Dock planks at 479.65–480.16 → above water
  - Village ground (deck) mean 479.19 → dry; buildings 479.54+ → dry
- Patch tool: `scripts/patch_water_xclw.py` (single 4-byte float swap, no record-size change)
- Repo + deployed ESP byte-identical (md5 2e252d166741a1492bbe8fd7e17be0f8)

## What we have

**Architecture:** Override Magnus's Morrowind WRLD (formID `0x0100E1C8`), override exterior cell (-1,-1) `0x010478A1`, persistent cell `0x0100E954`, add Seyda Neen LCTN (`0xFE000001`) as a sub-location of Morrowind_ID (`0x0100E774`).

**Records (verified 2026-08-06, deployed ESP = golden baseline):**
- 242 STAT records (fids `0xFE000100`–`0xFE0001F1`; 241 objects + `seyda_neen_terrain`)
- 435 exterior REFRs (fids `0xFE0001F2`+; 434 objects + terrain REFR `0xFE000647`) in 1 cell (-1,-1)
- 675 interior REFRs in 13 interior cells (fids `0xFE000648`+)
- 1 Seyda Neen LCTN (formID `0xFE000001`)
- Top-level order: STAT, CELL (interiors), WRLD, LCTN (CELL before WRLD)
- Exterior cell: DATA `0x202`, XCLC (-1,-1,0), **XCLW = FLT_MAX** (no water), uncompressed
- Persistent cell: compressed, DATA `0x2`, XCLC (0x7FFFFFFF,0x7FFFFFFF,0), XCLW = FLT_MAX

**Assets:**
- 242 converted Starfield NIFs in `converted_assets\meshes\`
- Terrain mesh `seyda_neen_terrain.nif` (505,626 B) + `temp_terrain_color.mat` + DDS — now in repo
- 179 .mat files in repo `Data\Materials\morrowind\` (418 deployed — 239 test/dupes)
- 96 original Morrowind DDS textures

**Files:**
- `C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp` (120,181 B, md5 b307ac466d)
- `C:\XboxGames\Starfield\Content\Data\SeydaNeen.esp` (deployed, byte-identical)

## What works

- **CK loads the mod** without errors (objects visible, correct positions)
- **Textures rendering** — buildings, furniture, clutter show Morrowind textures
- **Material chain complete** — NIF → .mat → .dds
- **Terrain material fixed 2026-08-06** — `temp_terrain_color.mat` had a CDB ID collision with `tx_bc_bank.mat` (identical `res:` IDs, both 4 components). Regenerated unique IDs; engine previously reported "can't be loaded".
- **Terrain static mesh** — 500×500 unit mesh, z 475.7–486.2, REFR at (-357.40, -348.00, 475.75), covers the town cluster

## What doesn't work yet

- **No LAND records** — terrain is a static mesh, not real landscape
- **No NPCs/creatures** — static objects only
- **No door teleportation** — interior ↔ exterior links not set up
- ~~**No water**~~ — **DONE 2026-08-06**: harbor cell XCLW = 479.0, persistent/interiors FLT_MAX/absent
- **No landscape textures** — ground is flat mesh, not Bitter Coast mud
- **No collision** — walk through walls/objects
- **No navmesh** — NPCs can't navigate

## Coordinate system (VERIFIED from deployed ESP, 2026-08-06)

- Morrowind uses **8192-unit cells**, Magnus's WRLD uses 100-unit cells (DNAM 200×160)
- Scale factor: `100 / 8192 ≈ 0.0122`
- **Actual offsets in deployed ESP:** `OFFSET_X=92.6`, `OFFSET_Y=802.0`, `Z_OFFSET=480.0`
  - x = x_mw × 0.0122 + 92.6, y = y_mw × 0.0122 + 802.0, z = z_mw × 0.0122 + 480.0
  - Verified: ex_nord_door_01 x_mw=-9821.382 → -27.29 ✓ (matches deployed REFR)
- **AGENTS.md's -1900/-1169/480 offsets are STALE** — match generate_btd.py v1-3, not the deployed ESP
- The deployed ESP z uses a local-z source (deployed z ≈ 480 + z_local×SCALE where z_local ∈ -26..23); the current placement CSV stores absolute z_mw (268–452) — **the golden ESP's exact generator is lost**

## Known generator regression (2026-08-06)

- `scripts/generate_full_seydaneen.py` (mtime 7/24) does **NOT** reproduce the deployed ESP:
  - Uses OFFSET_X=5986, OFFSET_Y=51539 (vs 92.6/802)
  - Spreads REFRs over 12 cells (-3,-8)..(-1,-4) (vs single cell (-1,-1))
  - Writes XCLW=0.0 (vs FLT_MAX) — would create a water plane
  - Orders WRLD before CELL (deployed: CELL before WRLD)
  - 241 STATs (missing terrain), REFR flags 0x00010400 (deployed: 0x0)
- Do NOT regenerate from this script expecting the deployed ESP. Treat deployed/committed ESP as golden.

## Material pipeline (RESOLVED)

1. **NIF material paths** — Set Blender material name before SGB export
2. **.mat files** — Clone Starfield template, swap texture paths, **regenerate unique CDB res IDs per file**
3. **DDS textures** — BC7 DX10 (dxgi 99), valid for Starfield
4. **CDB resource IDs** — must be unique per material; copying a template without re-randomizing IDs causes "ID collision" + "can't be loaded" errors (EditorWarnings confirms)

## Next steps (in order)

1. **Regenerate BTD terrain** — fix bbox bug in `generate_btd_v4.py` (was clamping to one cell), re-run with grid centered on data
2. **Test in-game** — use `cow 0200E1C8 -2050 -2070` (formID remapped for load order); check harbor water plane renders and village is dry
3. ~~**Add water**~~ — **DONE 2026-08-06** (XCLW=479.0 harbor cell; `scripts/patch_water_xclw.py`)
4. **Add collision** — Havok round-trip via `scripts\collision\` (hk_decode_lib.py, hk_polytope.py, hk_encode.py)
5. **Add door teleportation** — interior ↔ exterior links
6. **Add NPCs/creatures** — populate the town
7. **Scale to Vvardenfell** — expand beyond Seyda Neen

## Files in place

```
C:\XboxGames\Starfield\Content\Data\
├── SeydaNeen.esp                          # Main plugin (golden, 120,181 B)
├── meshes\morrowind\                      # 244 converted NIFs (242 + terrain + test)
├── Materials\morrowind\                   # 418 .mat files (179 core + dupes)
├── Textures\morrowind\                    # 96 DDS textures + terrain color
└── Terrain\Morrowind\Morrowind.btd        # 64-B stub (flat placeholder)
```
