# Phase 5: Starfield Creation Kit Assembly

**Estimated Time:** 20-30 hours
**Prerequisites:** Phase 3 (meshes) and Phase 4 (textures) complete

## Overview

Place all converted assets into Starfield using the Creation Kit.
Create the Seyda Neen cell, set up terrain, lighting, and integrate
with the Magnus mod's Morrowind province.

## Understanding Starfield CK Cell System

### Cell Types in Starfield

1. **Interior Cells** - Fully enclosed spaces (building interiors)
   - Fixed lighting, no weather
   - Loaded separately from exterior

2. **Exterior Cells** - Part of the planet surface
   - Subject to weather, day/night cycle
   - Connected to the planet's terrain system

3. **Worldspace Overlays** - Custom terrain patches
   - Mini-worldspaces stitched into procedural terrain
   - Give full control over terrain shape
   - Used by Starfield's hand-crafted locations

### How Magnus Structures Its Cells

The Magnus mod uses biome-based landing zones:
- Each province (Cyrodiil, Skyrim, Morrowind, etc.) is a biome
- Landing in a province biome loads a terrain section
- The terrain is generated from heightmap data
- Objects are placed on the generated terrain

**For Seyda Neen, we need to decide:**
1. Place objects directly on the generated terrain (simpler)
2. Create a worldspace overlay for full terrain control (better)
3. Create an interior cell accessed via a door (compromise)

## Step 5.1: Plan the Cell Layout

### Reference: Original Seyda Neen Layout

From Morrowind, Seyda Neen's layout (roughly):

```
                    [Lighthouse]
                         |
    [Fort Walls]----[Bridge]----[Census Office]
         |                         |
    [Houses]                  [Dock Area]
         |                         |
    [Arrille's Tradehouse]    [Docks]
         |
    [Road to Pelagiad]
```

**Key landmarks to place:**
1. Census and Excise Office (starting building)
2. Lighthouse (tall, visible landmark)
3. Fort walls (perimeter)
4. Bridge (over the river)
5. Dock structures
6. Arrille's Tradehouse
7. Several houses
8. Road connections

### Scale Considerations

Morrowind's Seyda Neen is relatively compact. In Starfield:
- Walking distance should feel similar
- Building spacing should match
- The dock should reach water

**Measure in CK:**
- 1 unit = ~1 meter
- Character height: ~1.8m
- Building height: ~3-5m typically
- Seyda Neen area: ~100m x 100m approximately

## Step 5.2: Open Magnus in the CK

1. Launch Starfield Creation Kit
2. File > Data
3. Check "The Elder Star System Magnus" as active plugin
4. Also check "Starfield.esm" as a master
5. Click OK (expect 5-10 minute load time)

**Navigate to Morrowind Province:**
1. Cell View window > Exterior Cells
2. Find the Morrowind province cell
3. Double-click to load in Render Window

**Note:** The exact cell name depends on how Magnus named it.
Look for cells containing "Morrowind," "Vvardenfell," or the
biome designation.

## Step 5.3: Choose Placement Strategy

### Strategy A: Direct Placement (Simplest)

Place objects directly on the existing terrain.

**Pros:**
- Simple, no terrain editing needed
- Works with existing Magnus biome
- Quick to set up

**Cons:**
- Limited control over terrain shape
- Terrain may not match Morrowind's Bitter Coast
- Objects may float or sink if terrain is uneven

**Best for:** Initial testing, proof of concept

### Strategy B: Worldspace Overlay (Recommended)

Create a mini-worldspace that defines custom terrain for Seyda Neen.

**Pros:**
- Full control over terrain shape
- Can match Morrowind's terrain accurately
- Professional quality

**Cons:**
- More complex setup
- Requires understanding worldspace overlays
- May conflict with Magnus's biome system

**Best for:** Final release quality

### Strategy C: Interior Cell (Compromise)

Create Seyda Neen as a large interior cell, accessed via a door/marker.

**Pros:**
- Complete control over environment
- No terrain conflicts
- Easier to light and decorate

**Cons:**
- Loses the outdoor feel
- No weather/day-night cycle
- Loading screen when entering

**Best for:** Testing, or if terrain integration proves too difficult

**Recommendation:** Start with Strategy A for testing, then move to
Strategy B for the final version.

## Step 5.4: Place Buildings (Strategy A)

### Import Converted Meshes

1. Object Window > Meshes
2. Navigate to your converted meshes folder
3. Or use: File > Data > Add your plugin as active

**If meshes aren't showing:**
- Ensure .nif and .mesh files are in the correct Data path
- Check that material paths are set correctly
- Restart CK after adding new files

### Building Placement Workflow

1. **Drag a mesh** from Object Window to Render Window
2. **Position it** using:
   - WASD for movement
   - Mouse for rotation
   - Or use the Inspector window for precise coordinates
3. **Snap to grid** if needed for alignment
4. **Repeat** for all building pieces

### Seyda Neen Building Order

Place in this order for logical assembly:

1. **Ground/floor pieces** - Foundation
2. **Walls** - Perimeter and interior
3. **Floor/ceiling** - Upper levels
4. **Roof** - Top covering
5. **Stairs/ramps** - Access between levels
6. **Windows/doors** - Openings
7. **Dock pieces** - Water-side structures
8. **Bridge** - River crossing

### Positioning Tips

- Use the Inspector window for exact XYZ coordinates
- Use the Render Window grid for alignment
- Press 'A' to toggle lighting for better visibility
- Press 'T' to center on selected object
- Use Shift+Mouse to orbit around selected object

## Step 5.5: Set Up Terrain

### Painting Ground Textures

If using Strategy A (direct placement):

1. Landscape Editing mode in CK
2. Select brush tool
3. Choose ground texture (bitter coast mud)
4. Paint the area where Seyda Neen sits
5. Add road textures for paths
6. Add grass/vegetation textures

### Terrain Sculpting (Strategy B)

If creating a worldspace overlay:

1. Create new Worldspace in CK
2. Set up terrain dimensions
3. Import or sculpt heightmap
4. Paint terrain textures
5. Stitch into Magnus's biome

**Note:** Terrain editing in Starfield CK is documented in the
Steam guide "Starfield Creation Kit: An Introductory Guide"
Section 15: Landscape Editing

## Step 5.6: Set Up Water

Seyda Neen has a harbor with water.

**In CK:**
1. Place a Water plane object
2. Position at the correct height (sea level)
3. Set water type (Bitter Coast water should be murky)
4. Adjust opacity and color

**Water properties to set:**
- Water type: Custom or reference existing
- Opacity: Semi-transparent
- Color: Greenish-brown (Bitter Coast style)
- Animated: Yes (waves/ripples)

## Step 5.7: Set Up Lighting

### Outdoor Lighting

1. **Sun/Light Source** - Uses Magnus's existing sun
2. **Time of Day** - Test at different times
3. **Ambient Light** - Adjust to match Morrowind's moody atmosphere

### Indoor Lighting

For building interiors:
1. Place Light objects inside buildings
2. Set color (warm yellow for torches, cool blue for magic)
3. Set intensity and radius
4. Add flickering effect for torches (optional)

### Bitter Coast Atmosphere

The Bitter Coast is:
- Overcast and foggy
- Dim lighting
- Greenish-brown tint
- Murky water

**Set up fog:**
- Fog density: Medium
- Fog color: Gray-green
- Near/far fog distances appropriate for the area

## Step 5.8: Create Map Marker

Add a map marker so players can fast-travel to Seyda Neen:

1. Place a MapMarker object
2. Set name: "Seyda Neen"
3. Set icon: Settlement/town icon
4. Set position: Center of the town
5. Link to the Magnus mod's Morrowind province

## Step 5.9: Add Navigation Mesh (Navmesh)

NPCs need navmesh to walk around.

1. Enter Navmesh editing mode
2. Generate navmesh for the cell
3. Verify it covers all walkable areas
4. Fix any holes or gaps
5. Test NPC pathing

**Navmesh tips:**
- Cover all floors and ground areas
- Include doorways and transitions
- Add jump markers for stairs/ramps
- Test with a test NPC

## Step 5.10: Testing in CK

Before testing in-game:

1. **Save your plugin** frequently
2. **Check for errors** in the CK log
3. **Render the cell** to verify visual appearance
4. **Run a cell check** for navmesh issues
5. **Test cell loading** by moving the player start

### Common CK Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Objects invisible | Missing material | Set material path in NifSkope |
| Objects black | Wrong material format | Check .mat file |
| Terrain holes | Navmesh gaps | Fix navmesh |
| CK crashes | Out of memory | Close other apps, save often |
| Can't find meshes | Wrong path | Check Data directory settings |

## Step 5.11: Link to Magnus

Our mod needs to depend on Magnus:

1. File > Data Masters
2. Add "The Elder Star System Magnus.esm" as a master
3. This ensures our mod loads after Magnus
4. We can reference Magnus's cells and objects

### Plugin Naming

```
SEY_SeydaNeen.esp  (or .esm)
```

**ESP vs ESM:**
- ESP: Regular plugin, easier to test
- ESM: Master file, required for complex dependencies
- Start with ESP, convert to ESM for release if needed

## Checklist

- [ ] CK opens with Magnus loaded
- [ ] Morrowind province cell identified
- [ ] All converted meshes are visible in Object Window
- [ ] All converted textures are applied correctly
- [ ] Buildings placed in correct layout
- [ ] Terrain painted with appropriate textures
- [ ] Water placed for harbor
- [ ] Lighting set up (outdoor + indoor)
- [ ] Map marker created
- [ ] Navmesh generated
- [ ] Plugin saved
- [ ] No CK errors in log

## Next Phase

Proceed to [Phase 6: NPCs & Dialogue](06-NPCS-CREATURES.md) to add
life to Seyda Neen.
