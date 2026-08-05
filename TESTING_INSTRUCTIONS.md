# Testing Instructions — Vvardenfell in Starfield

**Last Updated:** 2026-07-03

## What's Deployed

```
C:\XboxGames\Starfield\Content\Data\
├── SeydaNeen.esp                          # Main plugin (119,928 bytes)
├── meshes\morrowind\                      # 242 converted NIFs
├── Materials\morrowind\                   # 238 .mat files
└── Textures\morrowind\                    # 96 Morrowind DDS textures
```

## CK Testing

1. Launch CK via **CK High Priority** desktop shortcut
2. File → Data → select `SeydaNeen.esp`, check "Active", OK
3. Wait for load (may take a minute)
4. Cell View → Worldspace → "Morrowind"
5. Find "Surface" cell at grid (-1,-1) — double-click
6. Objects should appear with Morrowind textures in render window

### What to check in CK
- [ ] 434 objects visible in exterior cell (-1,-1)
- [ ] Objects show Morrowind textures (not purple/magenta)
- [ ] Objects positioned correctly (not floating/sunken)
- [ ] 13 interior cells accessible
- [ ] No errors in EditorWarnings.txt related to our mod

### CK Navigation Tips
- Press `A` to toggle lighting
- Press `T` to center on selected object
- Double-click objects in Cell View to focus camera
- Edit Properties window shows absolute world coordinates

## In-Game Testing

### Method: COW Command

1. Launch Starfield (NOT Creation Kit)
2. Load a save or start new game
3. Open console (`~` key)
4. Type: `cow 0200E1C8 -2050 -2070`
   - `0200E1C8` = Magnus's Morrowind WRLD formID (remapped for load order)
   - `-2050 -2070` = coordinates near Seyda Neen center
5. Press Enter

### Load Order

Correct load order:
```
Starfield.esm
The Elder Star System Magnus.esm
SeydaNeen.esp (our mod)
```

### What to check in-game
- [ ] Teleport works (loading screen appears)
- [ ] Objects visible after teleport
- [ ] Textures correct
- [ ] Scale feels right (buildings ~3-5m tall)
- [ ] No crashes

### If objects are invisible
- ESP may not be loading — check Plugins.txt has `*SeydaNeen.esp`
- Wrong coordinates — try different cow coordinates
- Load order issue — ensure Magnus loads before our mod

## Known Limitations

- **No terrain** — objects sit on Magnus's procedural ground
- **No NPCs** — static objects only
- **No collision** — walk through walls
- **No water** — harbor has no water plane
- **No navmesh** — NPCs can't navigate

## Logs & Debugging

- **CK errors:** `C:\XboxGames\Starfield\Content\EditorWarnings.txt`
- **CK crash dumps:** `C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.*.dmp`
- **ESP generator:** `scripts\generate_full_seydaneen.py`
