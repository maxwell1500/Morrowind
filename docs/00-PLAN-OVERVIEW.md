# Project Overview: Morrowind in Starfield

## What We're Building

A Starfield mod that recreates Morrowind's starting town **Seyda Neen** using
actual converted Morrowind assets. This serves as:
1. A playable location within The Elder Star System Magnus
2. A proof-of-concept for converting Morrowind assets to Starfield
3. A template for converting other Morrowind cities later

## Why Seyda Neen First

- **Small scope:** ~20-30 unique building meshes, ~15 NPCs
- **Iconic:** First location every Morrowind player sees
- **Manageable:** One of the smallest settlements in the game
- **Complete:** Has all required elements (docks, buildings, NPCs, creatures)

## Architecture: How Starfield Planets Work

### Starfield's Terrain System

Starfield does NOT use a single continuous world map like Skyrim. Instead:

1. **Planet View** - You see the planet from orbit with biome colored overlays
2. **Biomes** - Each planet has multiple biomes (forest, desert, tundra, etc.)
3. **Landing Zones** - You pick a spot within a biome to land
4. **Procedural Generation** - The terrain is generated at runtime based on:
   - A heightmap (R32 raw heightmap data)
   - Biome texture rules (which textures go where based on slope/altitude)
   - Placed objects (POIs, structures, flora, fauna)

### How Magnus Creates Nirn

The Elder Star System Magnus mod works by:

1. **Custom Planet Mesh** - A 3D model of Nirn with its own textures (since v5.0)
2. **Biome Definitions** - Each Tamriel province is a separate biome
   - Cyrodiil, Skyrim, Morrowind, Hammerfell, High Rock, etc. each get their own
3. **Heightmap Data** - Originally from transbot9's heightmap (Nexus), converted to
   R32 format by the user Deveris
4. **Biome Paint** - Grass, roads, snow, lava painted per province
5. **Landing Zones** - Map markers for each province
6. **Flat City Areas** - Intentionally flat zones where cities are meant to be built
7. **Roads** - Connecting paths between locations
8. **Random Peaks** - Terrain features elsewhere

### The Flat Terrain Situation

What you're seeing is BY DESIGN:
- **Flat landing zones** - Where ships touch down
- **Flat city areas** - Blank canvases for modders to build cities on
- **Roads** - Pre-painted paths connecting areas
- **Random peaks** - Decorative terrain features

The flat areas are intentionally empty for modders to fill with buildings
and custom terrain. This is exactly what we need.

### How Our City Plugs In

Starfield CK offers three approaches:

**Option A: Worldspace Overlay (RECOMMENDED)**
- Create a mini-worldspace that defines a custom terrain patch
- This REPLACES the procedural terrain underneath (not just overlays)
- Gives us full control over terrain shape, textures, and object placement
- Used by Starfield's own hand-crafted locations (New Atlantis, etc.)
- **Confirmed working** by community modders via Terrain > Export Landscape

**How it works:**
1. Create new Worldspace in CK (named to match your plugin)
2. Sculpt terrain using Landscape Editing tools
3. Export via Terrain > Export Landscape (saves to Data/Terrain/)
4. Archive terrain files in BA2
5. Export plugin - terrain override is included
6. Your terrain replaces Magnus's flat placeholder completely

**Option B: Build on Magnus's Flat Areas**
- Magnus has intentionally flat areas for cities
- Place objects directly on these flat zones
- Simpler, but limited terrain control
- Good for initial testing

**Option C: Interior Cell**
- Create Seyda Neen as an interior cell
- Load via a door/trigger
- Simplest but loses outdoor feel

**Recommendation:** Start with Option B (flat areas) for testing,
then move to Option A (worldspace overlay) for accurate terrain.

### The Asset Problem

**There are NO pre-converted Morrowind assets for Starfield.**

Every asset must be converted from scratch using the pipeline in Phase 3.
The only alternatives are:
1. Use Starfield's own assets as placeholders (build layout first)
2. Check Magnus Discord for community-shared assets
3. Use upscaled textures from Morrowind Enhanced Textures pack
4. Convert everything ourselves (the full pipeline)

The Imperial City mod proved this pipeline works (137+ hours for Oblivion
assets), but those were Oblivion-themed, not Morrowind-themed.

## Conversion Pipeline Summary

```
Morrowind BSA Files
        |
        v
    [Extract with BAE]
        |
        v
    Raw NIF meshes + DDS textures
        |
        v
    [Blender + Starfield Geometry Bridge]
    Import NIF -> Clean -> Export Starfield NIF + .mesh
        |
        v
    [AI Upscaler + Texconv]
    Upscale textures 2x/4x -> Convert to Starfield DDS format
        |
        v
    [NifSkope]
    Set material paths -> Create collision
        |
        v
    [Starfield Creation Kit]
    Sculpt terrain -> Place buildings -> Add NPCs -> Write dialogue
        |
        v
    [BAMgr / Archive2]
    Pack into BA2 archives -> Create ESP/ESM plugin
        |
        v
    Test in game -> Polish -> Release
```

## Scope Definition

### What's In Scope (Seyda Neen)

| Category | Count | Priority |
|----------|-------|----------|
| Building meshes | ~20-30 | High |
| Dock structures | 3-5 | High |
| Lighthouse | 1 | High |
| Clutter (barrels, crates) | ~15 | Medium |
| Furniture | ~10 | Medium |
| Clothing items | ~5-10 | Medium |
| Ground textures | ~10 | High |
| Building textures | ~20 | High |
| Water effects | 1 | High |
| Terrain sculpting | 1 area | High |
| NPCs | ~15-20 | High |
| Dialogue | ~100-200 lines | High |
| Ambient sounds | ~5-10 | Medium |
| Guar (pack animal) | 1 | Low |
| Silt Strider | 0 | Deferred |

### What's Deferred (Future Cities)

- Full creature conversions
- All weapons and armor
- Quest scripting
- Full voice acting
- Landscape overhaul for entire Vvardenfell

## Reusable Pipeline (For Future Cities)

Every step documented in phases 01-07 includes:
1. **Exact commands/tools used**
2. **Settings and parameters**
3. **Common pitfalls and solutions**
4. **Time estimates**
5. **Quality checklist**

This means when we do Balmora, Ald'ruhn, Vivec, etc., we follow the same
pipeline with different source assets.

### City Conversion Order (Recommended)

| Order | City | Size | Notes |
|-------|------|------|-------|
| 1 | Seyda Neen | Small | Starting town, most iconic |
| 2 | Caldera | Small | Nearby, shares some assets |
| 3 | Balmora | Medium | Iconic trading city |
| 4 | Ald'ruhn | Medium | Unique crab shell architecture |
| 5 | Molag Mar | Small | Ashlander-influenced |
| 6 | Sadrith Mora | Medium | Telvanni mushroom towers |
| 7 | Ebonheart | Small | Imperial fortress |
| 8 | Vivec City | Large | Massive - the "final boss" |

## Estimated Timeline

| Phase | Time Estimate | Dependencies |
|-------|--------------|--------------|
| Phase 1: Tool Setup | 2-4 hours | None |
| Phase 2: Asset Extraction | 1-2 hours | Phase 1 |
| Phase 3: Mesh Conversion | 20-40 hours | Phase 2 |
| Phase 4: Texture Conversion | 10-20 hours | Phase 2 |
| Phase 5: CK Assembly | 20-30 hours | Phase 3, 4 |
| Phase 6: NPCs & Dialogue | 10-15 hours | Phase 5 |
| Phase 7: Packaging & Testing | 5-10 hours | Phase 6 |
| **Total** | **~70-120 hours** | |

This is a serious project. The Imperial City mod took 137+ hours for asset
conversion alone. Seyda Neen is much smaller but still significant.

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mesh conversion issues | High | Study Imperial City mod, join Magnus Discord |
| No pre-converted assets exist | High | Full conversion pipeline required |
| Texture quality | Medium | Use existing upscaled packs as base |
| Terrain edge seams | Medium | Careful edge matching at worldspace boundaries |
| Performance issues | High | Optimize LODs, use BA2 compression |
| Starfield updates break things | Medium | Pin to specific version, monitor patches |
| Scope creep | High | Stick to Seyda Neen only for v1 |
