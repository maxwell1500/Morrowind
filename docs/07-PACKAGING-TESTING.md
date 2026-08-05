# Phase 7: Packaging, Testing & Release

**Estimated Time:** 5-10 hours
**Prerequisites:** All previous phases complete

## Overview

Package all assets into BA2 archives, create the final plugin, test
thoroughly, and prepare for release.

## Step 7.1: Organize Final Assets

### File Structure for Release

```
Data\
├── SEY_SeydaNeen.esm (or .esp)
├── SEY_SeydaNeen - Textures.ba2
├── SEY_SeydaNeen - Meshes.ba2
├── SEY_SeydaNeen - Sounds.ba2 (if applicable)
└── planetdata\
    └── biomemaps\
        └── [biome files] (if creating custom biome)
```

**Naming convention:**
- Plugin: `SEY_SeydaNeen.esp` (or .esm)
- BA2 archives must match plugin name prefix
- BA2 files are named: `[PluginName] - [ContentType].ba2`

## Step 7.2: Create BA2 Archives

### Using BAMgr

1. Launch BAMgr.exe
2. File > New Archive
3. Add files from `converted_assets/meshes/`
4. Save as `SEY_SeydaNeen - Meshes.ba2`

**BAMgr Settings:**
- Archive version: 2 (Starfield)
- Compression: None (for meshes, better loading)
- Format: Check "Create assistance" for optimal settings

### Using Archive2 (Alternative)

1. Open Archive2 from Starfield's Tools folder
2. File > New
3. Add files
4. Save with correct naming

### What Goes in Each Archive

| Archive | Contents | Compression |
|---------|----------|-------------|
| Meshes.ba2 | .nif, .mesh files | None |
| Textures.ba2 | .dds texture files | None (or optional) |
| Materials.ba2 | .mat material files | None |
| Sounds.ba2 | .wav, .wem audio files | None |

**Important:** Do NOT compress meshes or textures in BA2. Compression
causes slower loading and potential crashes. Leave them uncompressed.

## Step 7.3: Final Plugin Setup

### Verify Masters

In CK, verify your plugin's master files:

1. File > Data Masters
2. Ensure "Starfield.esm" is listed
3. Ensure "The Elder Star System Magnus.esm" is listed
4. No other unintended masters

### Verify All Records

Check that your plugin contains all necessary records:

| Record Type | What to Check |
|-------------|---------------|
| CELL | Your Seyda Neen cell exists |
| NPC_ | All NPCs are created |
| DIAL | All dialogue topics exist |
| PACK | All AI packages exist |
| LVLC | Leveled creature lists (if any) |
| WEAP | Weapons (if any) |
| ARMO | Armor (if any) |
| CLOTH | Clothing items |
| STAT | Static objects |

### Plugin Size Check

- ESP plugins: Limited to 253 full masters in load order
- For a single city mod, ESP is fine
- Convert to ESM if making this a master for other mods

## Step 7.4: Testing Protocol

### Test 1: Basic Loading

1. Install the mod (copy files to Starfield Data)
2. Launch Starfield via SFSE
3. Open console (~) and type:
   ```
   coc "SEY_SeydaNeen" [cell name]
   ```
   Or travel to the location through Magnus
4. Verify the cell loads without crash

### Test 2: Visual Inspection

Walk through the cell and check:
- [ ] All buildings appear correctly
- [ ] Textures are applied and look right
- [ ] Lighting works (day and night)
- [ ] Water appears and animates
- [ ] No black/pink/missing textures
- [ ] No obvious z-fighting or flickering

### Test 3: NPC Verification

- [ ] All NPCs are present
- [ ] NPCs are in correct positions
- [ ] NPCs are wearing correct clothing
- [ ] NPCs have facegen (not default face)
- [ ] NPCs idle correctly
- [ ] NPCs walk their routes

### Test 4: Dialogue Testing

Talk to each NPC and verify:
- [ ] Greeting dialogue plays
- [ ] All dialogue options work
- [ ] No broken dialogue links
- [ ] Quest dialogue triggers correctly (if applicable)

### Test 5: Performance

- [ ] Frame rate is acceptable (30+ FPS)
- [ ] No major stuttering when entering area
- [ ] Loading time is reasonable
- [ ] No memory leaks (extended play)

### Test 6: Compatibility

Test with these mods loaded:
- [ ] Elder Star System Magnus (required)
- [ ] Imperial City of Cyrodiil (should not conflict)
- [ ] Other popular mods (StarUI, etc.)

### Test 7: Edge Cases

- [ ] Enter/exit all buildings
- [ ] Walk to all edges of the cell
- [ ] Swim in the water
- [ ] Fast travel to/from the location
- [ ] Save and load the game in the cell
- [ ] Wait/sleep to advance time
- [ ] Check console for error messages

## Step 7.5: Debug Common Issues

### "Black textures in-game"

**Cause:** Material path incorrect or .mat file missing
**Fix:**
1. Open the .nif in NifSkope
2. Verify material path matches your .mat file location
3. Check .mat file is valid JSON

### "Pink/missing meshes"

**Cause:** .nif or .mesh file not found
**Fix:**
1. Verify files are in correct Data path
2. Check BA2 is named correctly and loaded
3. Check file names match references in plugin

### "NPCs not appearing"

**Cause:** NPC placement reference broken
**Fix:**
1. Open NPC record in CK
2. Verify cell reference is correct
3. Check enable state (should be enabled)

### "Dialogue not triggering"

**Cause:** Dialogue conditions not met
**Fix:**
1. Check dialogue conditions in CK
2. Verify topic links are correct
3. Check for duplicate topic IDs

### "CK crashes when loading"

**Cause:** Corrupt plugin or missing master
**Fix:**
1. Verify all masters are present
2. Try loading the plugin alone
3. Check CK log for specific error
4. Revert to last good save

## Step 7.6: Performance Optimization

### LOD Generation

Ensure LoD meshes are included for all buildings. LoD allows the game
to render simplified versions at distance, improving performance.

### Texture Optimization

If performance is poor:
1. Reduce texture resolution from 4K to 2K
2. Use BC7 compression instead of uncompressed
3. Reduce number of unique textures (reuse where possible)

### Object Optimization

- Use instances where possible (not unique copies)
- Merge small objects into larger meshes
- Remove invisible/unnecessary objects

## Step 7.7: Create Release Package

### File Checklist

```
SEY_SeydaNeen_v1.0.zip
├── Data\
│   ├── SEY_SeydaNeen.esm
│   ├── SEY_SeydaNeen - Meshes.ba2
│   ├── SEY_SeydaNeen - Textures.ba2
│   └── SEY_SeydaNeen - Sounds.ba2 (if applicable)
├── README.md
├── INSTALL.md
└── CHANGELOG.md
```

### README Content

Include in your release README:
1. Mod name and version
2. Description
3. Requirements (Magnus, SFSE, etc.)
4. Installation instructions
5. Compatibility notes
6. Known issues
7. Credits
8. Permissions

### Installation Instructions

```
1. Install The Elder Star System Magnus (required)
2. Install Starfield Script Extender (SFSE)
3. Extract this archive to your Starfield Data folder
4. Add to StarfieldCustom.ini:
   [Archive]
   sResourceDataDirsFinal=SEY_SeydaNeen\
5. Launch via SFSE
6. Travel to the Elder Star System > Nirn > Morrowind > Seyda Neen
```

## Step 7.8: Upload to Nexus Mods

### Preparation

1. Take screenshots (exterior, interior, NPCs, dialogue)
2. Write mod description
3. Tag appropriately (Planets, Locations)
4. Set requirements (Magnus)

### Upload

1. Log into nexusmods.com
2. Submit new mod for Starfield
3. Upload the zip file
4. Add images and description
5. Set permissions (allow modification, conversion)
6. Submit for approval

## Step 7.9: Post-Release

### Monitor

- Check comments for bugs
- Respond to user questions
- Track endorsement/downloads

### Plan Updates

- v1.1: Bug fixes based on feedback
- v1.2: Add missing features
- v2.0: Major additions (more NPCs, quests, etc.)

## Checklist

- [ ] All assets in BA2 archives
- [ ] Plugin verified in CK
- [ ] Basic loading test passed
- [ ] Visual inspection passed
- [ ] NPC verification passed
- [ ] Dialogue testing passed
- [ ] Performance acceptable
- [ ] Compatibility tested
- [ ] Release package created
- [ ] README and INSTALL written
- [ ] Screenshots taken
- [ ] Uploaded to Nexus

## Completion

Congratulations! You've successfully converted Morrowind assets to
Starfield and built Seyda Neen.

**Document everything in LESSONS-LEARNED.md for future cities.**

## Next Steps

- Apply this pipeline to other Morrowind cities
- Balmora (next logical city - larger but iconic)
- Caldera (nearby, shares some assets)
- Vivec City (massive undertaking - the "final boss")
