# Vvardenfell Mod — Status (2026-07-03)

## What we have

**Architecture:** Override Magnus's Morrowind WRLD (formID `0x0100E1C8`), override cells at grid (-1,-1), add Seyda Neen LCTN as a sub-location of Morrowind_ID.

**Records:**
- 241 STAT records (Morrowind objects with converted NIFs)
- 434 exterior REFRs in 1 cell (-1,-1) (overrides Magnus's cell)
- 13 interior cells with 675 REFRs
- 1 Seyda Neen LCTN (formID 0xFE000001)

**Assets:**
- 242 converted Starfield NIFs with correct material paths
- 238 .mat files (cloned from Starborn template, texture paths swapped)
- 96 original Morrowind DDS textures in `Data\Textures\morrowind\`

**Files:**
- `C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp` (119,928 bytes)
- `C:\XboxGames\Starfield\Content\Data\SeydaNeen.esp` (deployed)

## What works

- **CK loads the mod** without errors
- **Objects visible** in CK render window with correct positions
- **Textures rendering** — buildings, furniture, clutter all show Morrowind textures
- **Material chain complete** — NIF → .mat → .dds → file exists
- **241 unique meshes** converted from Morrowind to Starfield format

## What doesn't work yet

- **No terrain** — objects sit on Magnus's procedural terrain (may float/sink)
- **No NPCs/creatures** — static objects only
- **No door teleportation** — interior ↔ exterior links not set up
- **No water** — harbor area has no water plane
- **No landscape textures** — ground is Magnus's default, not Bitter Coast mud
- **No collision** — walk through walls/objects
- **No navmesh** — NPCs can't navigate

## Scale system

- Morrowind uses **8192-unit cells**, Magnus uses **100-unit cells**
- Scale factor: `100 / 8192 ≈ 0.0122`
- Current offsets: `OFFSET_X=-1900`, `OFFSET_Y=-1169`, `Z_OFFSET=480`
- All coordinates scaled before offset application

## Material pipeline (RESOLVED)

1. **NIF material paths** — Set Blender material name before SGB export
2. **.mat files** — Clone Starborn template, swap texture file paths only
3. **DDS textures** — Original Morrowind textures (not upscaled) in `Data\Textures\morrowind\`
4. **CDB resource IDs** — Must use valid IDs from Starfield's compiled database

## Key discoveries

- Starfield .mat files require valid CDB resource IDs — made-up IDs cause "no layer" errors
- Cloning a working Starfield .mat and changing only texture paths is the reliable approach
- `bUseCompiledDB=0` in CreationKitCustom.ini causes CK crashes
- Original Morrowind textures work in Starfield without upscaling
- SGB DLL crashes on multi-geometry NIFs — setting material BEFORE export avoids this

## Next steps (in order)

1. **Adjust Z offset** — objects may need height adjustment for terrain
2. **Test in-game** — use `cow` command to teleport to cell
3. **Add terrain** — LAND records with Morrowind ground textures
4. **Add water** — water plane for harbor area
5. **Add NPCs/creatures** — populate the town
6. **Add collision** — physics for walkability
7. **Scale to Vvardenfell** — expand beyond Seyda Neen

## Files in place

```
C:\XboxGames\Starfield\Content\Data\
├── SeydaNeen.esp                          # Main plugin
├── meshes\morrowind\                      # 242 converted NIFs
├── Materials\morrowind\                   # 238 .mat files
└── Textures\morrowind\                    # 96 Morrowind DDS textures
```
