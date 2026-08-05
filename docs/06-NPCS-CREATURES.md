# Phase 6: NPCs, Creatures & Dialogue

**Estimated Time:** 10-15 hours
**Prerequisites:** Phase 5 complete (cell is built and placeable)

## Overview

Populate Seyda Neen with NPCs using Starfield character templates
dressed in converted Morrowind clothing. Write dialogue that fits
Starfield's setting while honoring Morrowind's story.

## NPC Philosophy for This Project

**Key principle:** Use Starfield's existing NPC system, not Morrowind's.

- Starfield NPCs use facegen, voice types, and AI packages
- We dress them in converted Morrowind clothing
- Dialogue references both Morrowind lore and Starfield context
- This creates a "Starfield version of Seyda Neen" not a 1:1 recreation

## Step 6.1: Plan NPC List

### Essential NPCs for Seyda Neen

| NPC Name | Role | Race | Notes |
|----------|------|------|-------|
| **Caius Cosades** | Blades contact | Imperial | Key quest NPC |
| **Fargoth** | Racist shopkeeper | Dunmer | Iconic character |
| **Aristotle Moral** | Census officer | Imperial | Starting quest |
| **Vedam Dren** | Hlaalu noble | Dunmer | Local authority |
| **Hrisskar Flat-Foot** | Guard captain | Imperial | Security |
| **Darvam Hlan** | Dock worker | Dunmer | Atmosphere |
| **Llirala Maren** | Healer | Dunmer | Services |
| **Arrille** | Tradehouse owner | Altmer | Shop |
| **Sjoring Hard-Heart** | Fighter's Guild | Nord | Quest giver |
| **Several townsfolk** | Background NPCs | Mixed | Atmosphere |

**Total: ~15-20 NPCs**

## Step 6.2: Create NPCs in CK

### NPC Creation Workflow

1. **Object Window > NPC** (or Character > NPC)
2. **Right-click > New** to create a new NPC
3. **Set properties:**

### NPC Properties to Configure

| Property | Value | Notes |
|----------|-------|-------|
| Name | [NPC name] | Display name |
| Race | Dunmer/Imperial/Altmer/Nord | Match lore |
| Level | 5-25 | Based on role |
| Base Health | 100-300 | Based on level |
| Base Magicka | 50-150 | Based on class |
| Class | Custom or reference | See below |
| Faction | House Hlaalu, Imperial, etc. | Based on role |
| Package | AI package | Behavior |
| Outfit | Converted Morrowind clothing | Visual identity |

### Class Setup

For each NPC, assign a class (or create custom):

**Caius Cosades:**
- Class: Scout/Agent
- Skills: Sneak, Marksman, Speechcraft
- Level: 20+

**Fargoth:**
- Class: Merchant
- Skills: Mercantile, Speechcraft
- Level: 10

**Aristotle Moral:**
- Class: Noble/Bureaucrat
- Skills: Speechcraft, Mercantile
- Level: 15

### AI Packages

Set up basic AI for each NPC:

1. **Idle package** - Stand in their location
2. **Sand package** - Wander within their area
3. **Sleep package** - Go to bed at night (if applicable)
4. **Work package** - Do their job during the day

**In CK:**
- Object Window > Packages
- Create new package for each NPC behavior
- Link to NPC and set schedule

## Step 6.3: Dress NPCs in Morrowind Clothing

### Convert Key Clothing Items

From Phase 3, convert these clothing meshes:

| Clothing | For NPC | Priority |
|----------|---------|----------|
| Common clothes (male) | Townsfolk, Fargoth | High |
| Common clothes (female) | Townsfolk, Llirala | High |
| Noble clothes | Vedam Dren | Medium |
| Imperial uniform | Guards, Census office | Medium |
| robes | Healers, Temple | Low |

### Equip NPCs with Clothing

1. In NPC properties, find "Outfit" or "Worn Items"
2. Add converted Morrowind clothing items
3. For armor/weapons: Add if the NPC should carry them

**Note:** Starfield's outfit system may differ from Morrowind's.
Check how Starfield NPCs are dressed in existing game data.

## Step 6.4: Write Dialogue

### Dialogue Philosophy

Our dialogue should:
1. Reference Morrowind lore naturally
2. Acknowledge Starfield's sci-fi setting
3. Feel like what these characters would say in Starfield's universe
4. Not just copy Morrowind dialogue verbatim

### Example Dialogue

**Caius Cosades (greeting the player):**
```
"Ah, you must be the new agent. I've been waiting.
The Blades have been tracking activity on this rock
for months. Welcome to Vvardenfell - what's left of it.
Word of advice: don't trust anyone who offers you
a free ride to the Ministry of Truth."
```

**Fargoth (if player is not Dunmer):**
```
"Another outlander, I see. Come to buy, or just
to breathe our air? If you're looking for supplies,
you've come to the right place. If you're looking
for trouble, you've also come to the right place.
Prices are higher for non-Dunmer. That's just
how it works."
```

**Aristotle Moral (census processing):**
```
"Name and citizenship status, please. You're here
under the Empire's dispensation, so we'll need to
process your documentation. Don't worry, it's
routine. Just... don't mention the name Nerevarine
while you're here. Some people get nervous."
```

### Dialogue Structure in CK

1. **Object Window > Dialogue**
2. **Create new dialogue topic**
3. **Set conditions** (who says it, when)
4. **Add response lines**
5. **Link to other topics** for conversation trees

### Dialogue Categories

| Type | Purpose | Example |
|------|---------|---------|
| Hello/Greeting | First interaction | "Welcome to Seyda Neen" |
| Idle | Random comments | "The water's been rough lately" |
| Info | Lore/information | "This town was founded by..." |
| Quest | Quest-related | "I need you to deliver this" | Services | Shop/services | "Take a look at my wares" |

## Step 6.5: Creatures

### What to Include

For Seyda Neen, the most important creature is the **guar** - the pack
animal that's iconic to Morrowind.

**Options:**
1. **Re-skin a Starfield creature** - Find a similar creature and change textures
2. **Convert the Morrowind guar mesh** - Full conversion like buildings
3. **Skip creatures for v1** - Use Starfield creatures or none

**Recommendation for v1:** Skip guar conversion. Use a Starfield creature
as a stand-in, or place a non-interactive guar model as decoration.

### Converting Guar (If Desired)

The guar is a relatively simple quadruped creature:
1. Convert NIF mesh (same pipeline as buildings)
2. Convert textures (same pipeline)
3. Set up animation (complex - may need to use Starfield creature animations)
4. Create NPC/creature entry in CK

**Note:** Creature animation is significantly more complex than static meshes.
This may be deferred to a later version.

## Step 6.6: Ambient Life

### Market Stalls

Place market stall objects with clutter:
- Sacks, barrels, crates
- Food items
- Clothing on display

### Dock Details

- Rope coils
- Fishing nets
- Crates and barrels
- Boats (static models)

### Town Details

- Street lamps/torches
- Signs
- Bench/seating
- Decorative plants

## Step 6.7: Sound Design

### Ambient Sounds

Set up ambient sound emitters:

| Sound | Location | Volume |
|-------|----------|--------|
| Water lapping | Dock area | Medium |
| Seagulls | Harbor | Low |
| Town chatter | Central area | Low |
| Wind | Throughout | Low |
| Torch crackle | Near torches | Low |

### Music

- Use Magnus's existing music setup
- Or add Morrowind music tracks to the area

**Adding music in CK:**
1. Create a Music Marker
2. Set music type (exploration, combat, etc.)
3. Add custom music files if desired

## Step 6.8: Testing NPCs

### In-CK Testing

1. Place a player start marker in Seyda Neen
2. Move player to the cell
3. Walk around and verify:
   - NPCs are visible
   - NPCs are in correct positions
   - Clothing is applied correctly
   - Dialogue triggers properly
   - NPCs walk their routes (navmesh working)

### Common NPC Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| NPC T-posing | Missing skeleton | Check skeleton path |
| NPC invisible | Missing facegen | Generate facegen in CK |
| NPC stuck | Bad navmesh | Fix navmesh in that area |
| No dialogue | Topic not linked | Check dialogue conditions |
| Wrong clothing | Item not found | Verify clothing mesh exists |

## Checklist

- [ ] All NPCs created in CK
- [ ] NPC classes/skills assigned
- [ ] NPC factions set correctly
- [ ] Clothing items assigned to each NPC
- [ ] AI packages created and assigned
- [ ] Dialogue written for all NPCs
- [ ] Dialogue topics linked correctly
- [ ] Creatures placed (or deferred)
- [ ] Ambient sounds set up
- [ ] Test NPC pathing in CK

## Next Phase

Proceed to [Phase 7: Packaging & Testing](07-PACKAGING-TESTING.md)
to prepare for release.
