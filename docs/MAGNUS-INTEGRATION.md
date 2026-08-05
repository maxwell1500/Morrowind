# Magnus Integration Guide

**Purpose:** How our Seyda Neen mod integrates with The Elder Star System Magnus.

## How Magnus Works (Technical)

### Planet Nirn Structure

The Elder Star System Magnus creates planet Nirn using:

1. **Custom Planet Mesh**
   - A 3D sphere model with Nirn's continental outlines
   - Has its own textures and materials (since v5.0)
   - Visible from orbit when approaching the planet

2. **Biome System**
   - Each Tamriel province is defined as a separate biome
   - Biomes control terrain generation, textures, and flora
   - Provinces: Cyrodiil, Skyrim, Morrowind, Hammerfell, High Rock, etc.

3. **Heightmap Data**
   - Originally from transbot9's heightmap (Nexus Mods)
   - Converted to R32 format by user Deveris
   - Defines terrain elevation for the entire continent
   - This is why terrain has elevation variation (mountains, valleys)

4. **Biome Paint**
   - Grass, roads, snow, lava painted per biome
   - Uses Starfield's biome paint system
   - Updated iteratively (multiple "terrain passes")

5. **Landing Zones**
   - Map markers for each province
   - Player can land at any province marker
   - Landing triggers terrain generation for that area

### Morrowind Province in Magnus

The Morrowind province biome is located on the Vvardenfell portion
of the continent. Key characteristics:

- **Biome type:** Bitter Coast / Ashlands blend
- **Terrain:** Volcanic with some green areas
- **Special features:** Red Mountain lava, Silt Strider paths
- **Current state:** Basic terrain, no buildings (except preview assets)

### Where Seyda Neen Fits

Seyda Neen is located on the southern coast of Vvardenfell, near the
border with the Bitter Coast region. In Magnus:

- It falls within the Morrowind province biome
- The terrain near the coast should be relatively flat (docks area)
- The area should have Bitter Coast-style ground textures

## Integration Approaches

### Approach A: Worldspace Overlay (Recommended)

Create a mini-worldspace that overlays the terrain at Seyda Neen's location.

**How it works:**
1. Create a new worldspace in CK (e.g., "SEY_SeydaNeen")
2. Define terrain dimensions (e.g., 512x512 meters)
3. Sculpt terrain to match Morrowind's Seyda Neen
4. Place all buildings, NPCs, objects
5. Link the worldspace to Magnus's Morrowind biome

**In CK:**
```
Worldspace > New > SEY_SeydaNeen
  - Parent: [Morrowind biome cell]
  - Offset: [coordinates matching Seyda Neen location]
  - Size: [appropriate for the town]
```

**Pros:**
- Full control over terrain
- Can match Morrowind's layout exactly
- Professional quality

**Cons:**
- More complex setup
- Need to determine exact coordinates
- May need Magnus author cooperation for best results

### Approach B: Direct Placement

Place objects directly on Magnus's generated terrain.

**How it works:**
1. Load Magnus's Morrowind province cell
2. Place objects at the correct coordinates
3. Adjust object positions to match terrain height

**Pros:**
- Simple, no terrain editing
- Works with existing Magnus biome
- Quick to implement

**Cons:**
- Limited terrain control
- Objects may not align perfectly
- Terrain shape is whatever Magnus generates

**Best for:** Initial testing and proof of concept

### Approach C: Interior Cell (Alternative)

Create Seyda Neen as a large interior cell.

**How it works:**
1. Create interior cell "SEY_SeydaNeenInterior"
2. Build the entire town inside
3. Place a door/marker in Magnus's exterior
4. Player enters through the door

**Pros:**
- Complete control over environment
- No terrain conflicts
- Easier to light

**Cons:**
- Loses outdoor feel
- No weather/day-night
- Loading screen

**Best for:** Fallback if other approaches fail

## Coordinate System

### Finding Seyda Neen's Location on Magnus

To place Seyda Neen correctly, we need to know where it falls on
Magnus's planet.

**Methods:**
1. **In-game scouting:** Load Magnus, fly to Morrowind province, note coordinates
2. **CK inspection:** Open Magnus's cells in CK, find the Morrowind area
3. **Ask the Magnus community:** Join the Discord (discord.gg/njnSbYsrCA)

**Coordinate reference:**
- Morrowind is the eastern portion of Tamriel
- Seyda Neen is on the southern coast of Vvardenfell
- It should be near the water edge of the Morrowind biome

### Cell Coordinates in Starfield

Starfield uses a cell grid system:
- Each cell is 4096x4096 units
- Coordinates are [gridX, gridY]
- Height is separate (Z axis)

**For Seyda Neen:**
- We need to identify which cell(s) the town occupies
- Likely spans 1-4 cells depending on size

## Working With the Magnus Team

### Communication

The Magnus project has an active Discord:
- **Invite:** discord.gg/njnSbYsrCA
- **Purpose:** Development discussion, asset sharing, coordination

**Recommended approach:**
1. Join the Discord
2. Introduce yourself and your project
3. Ask about Morrowind province cell coordinates
4. Ask if any Morrowind assets have already been converted
5. Share your progress and get feedback

### Asset Sharing

The Magnus team may have already converted some assets that could
be shared or referenced. The Imperial City mod converted assets from
Rigmor of Cyrodil - similar approach could work for Morrowind assets.

### Permission and Credits

From Magnus permissions:
- "You are allowed to modify my files and release bug fixes or improve
  on the features so long as you credit me as the original creator"
- "You are allowed to use the assets in this file without permission
  as long as you credit me"

**Our mod should:**
- Credit RONALDMCDONLD (Magnus author)
- Credit the Imperial City mod for conversion techniques
- List Magnus as a requirement
- Not redistribute Magnus assets

## Terrain Considerations

### The Flat Terrain Issue

You mentioned the terrain looks flat on the planet. This is likely because:

1. **Heightmap resolution:** The original heightmap captures large-scale
   elevation (continent shape) but not fine detail (individual hills)

2. **Biome scaling:** Starfield scales terrain features based on planet
   size. Small variations may not be visible at orbit view.

3. **Landing area vs planet:** The terrain you walk on is a generated
   section, not the full planet surface. The planet mesh is visual only.

4. **Iteration needed:** The Magnus changelog mentions "terrain passes"
   suggesting terrain is refined over time.

### What This Means for Seyda Neen

- The terrain where we place buildings may be relatively flat
- This is actually GOOD for building placement
- We can add detail through object placement
- We can sculpt terrain within our worldspace overlay

### Future Terrain Improvements

If the Magnus team improves the heightmap:
- Higher resolution heightmap = more terrain detail
- More biome paint passes = better ground textures
- Community contributions welcome

## Testing Integration

### Test Checklist

- [ ] Magnus loads correctly with our mod
- [ ] Our mod appears after Magnus in load order
- [ ] Seyda Neen cell is accessible from Magnus's Morrowind biome
- [ ] Traveling to Seyda Neen works (fast travel, walking)
- [ ] No conflicts with Magnus's other features
- [ ] Imperial City mod doesn't conflict
- [ ] Performance is acceptable with both mods loaded

### Load Order

Correct load order should be:
```
Starfield.esm
The Elder Star System Magnus.esm
SEY_SeydaNeen.esp (our mod)
[Other mods]
```

Our mod loads AFTER Magnus because we depend on it.

### Conflict Resolution

If there are conflicts:
1. Check which records overlap
2. Use xEdit to merge or forward changes
3. Contact Magnus team if it's a Magnus issue
4. Document any workarounds in LESSONS-LEARNED.md

## Future Cities Integration

When adding more cities (Balmora, Vivec, etc.):

1. Each city gets its own plugin (SEY_Balmora.esp, etc.)
2. Each depends on Magnus
3. They can share common assets (clothing, textures)
4. Consider a merged plugin for all Morrowind cities

**Plugin naming:**
```
SEY_SeydaNeen.esp    - Starting town
SEY_Balmora.esp      - Next city
SEY_Vivec.esp        - Major city
SEY_Morrowind.esp    - Merged plugin (optional)
```
