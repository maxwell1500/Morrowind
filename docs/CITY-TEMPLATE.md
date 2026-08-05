# City Conversion Template

**Purpose:** Reusable template for converting any Morrowind city to Starfield.
Copy this file and fill in city-specific details for each new city.

---

## City: [CITY NAME]

### Overview

| Property | Value |
|----------|-------|
| **City Name** | [Name] |
| **Province** | [Morrowind/Oblivion/Skyrim] |
| **Region** | [Bitter Coast/Ashlands/Ascadian Isles/etc.] |
| **Size** | [Small/Medium/Large] |
| **Unique Buildings** | [count] |
| **Estimated Time** | [hours] |
| **Priority** | [High/Medium/Low] |

### City Description

[Brief description of the city, its significance, and what makes it unique]

### Reference Sources

| Source | URL | Notes |
|--------|-----|-------|
| UESP Wiki | uesp.net/wiki/Morrowind:[City] | Layout, NPCs, quests |
| Fandom Wiki | elderscrolls.fandom.com/wiki/[City] | Lore, characters |
| YouTube | [walkthrough link] | Visual reference |
| Screenshots | [image links] | Building references |

---

## Asset Inventory

### Buildings

| # | Building Name | NIF File(s) | Texture Files | Priority |
|---|---------------|-------------|---------------|----------|
| 1 | [Name] | [file.nif] | [file.dds] | High |
| 2 | [Name] | [file.nif] | [file.dds] | High |
| 3 | [Name] | [file.nif] | [file.dds] | Medium |

### Unique Structures

| # | Structure Name | NIF File(s) | Notes |
|---|----------------|-------------|-------|
| 1 | [Name] | [file.nif] | [description] |

### Furniture & Clutter

| # | Item Name | NIF File(s) | Reusable? |
|---|-----------|-------------|-----------|
| 1 | [Name] | [file.nif] | Yes/No |

### Textures

| # | Texture Name | Original Size | Target Size | Category |
|---|--------------|---------------|-------------|----------|
| 1 | [name.dds] | 64x64 | 2K | Ground |
| 2 | [name.dds] | 128x128 | 2K | Building |

### Clothing/Armor

| # | Item Name | NIF File(s) | For NPC |
|---|-----------|-------------|---------|
| 1 | [Name] | [file.nif] | [NPC] |

---

## NPC List

| # | Name | Race | Class | Level | Role | Clothing |
|---|------|------|-------|-------|------|----------|
| 1 | [Name] | [Race] | [Class] | [Lvl] | [Role] | [Item] |
| 2 | [Name] | [Race] | [Class] | [Lvl] | [Role] | [Item] |

### NPC Dialogue Summary

| NPC | Dialogue Topics | Quest Lines |
|-----|----------------|-------------|
| [Name] | [topics] | [quests] |

---

## Terrain & Environment

### Ground Textures Needed

| Texture | Source | Priority |
|---------|--------|----------|
| [Name] | [Morrowind or custom] | High |

### Water Setup

| Property | Value |
|----------|-------|
| Water type | [Bitter Coast/Standard/Custom] |
| Color | [RGB values] |
| Opacity | [0-1] |

### Lighting

| Property | Value |
|----------|-------|
| Atmosphere | [Clear/Overcast/Foggy] |
| Fog density | [None/Low/Medium/High] |
| Fog color | [RGB values] |
| Ambient tint | [RGB values] |

### Sound

| Sound | Location | Source |
|-------|----------|--------|
| [Sound] | [Location] | [Morrowind or custom] |

---

## Conversion Progress

### Meshes

| # | Building | Status | Notes |
|---|----------|--------|-------|
| 1 | [Name] | [Not Started/In Progress/Done] | [notes] |

### Textures

| # | Texture | Status | Notes |
|---|---------|--------|-------|
| 1 | [Name] | [Not Started/In Progress/Done] | [notes] |

### NPCs

| # | NPC | Status | Notes |
|---|-----|--------|-------|
| 1 | [Name] | [Not Started/In Progress/Done] | [notes] |

### Assembly

| Task | Status | Notes |
|------|--------|-------|
| Cell created | [ ] | |
| Buildings placed | [ ] | |
| Terrain painted | [ ] | |
| Water set up | [ ] | |
| Lighting done | [ ] | |
| Navmesh done | [ ] | |
| Testing done | [ ] | |

---

## Reusable Assets

Assets that can be shared with other cities:

| Asset | Type | Also Used In |
|-------|------|--------------|
| [Name] | [Mesh/Texture] | [Other cities] |

---

## Lessons for This City

Document what you learn specific to this city:

### What Worked

- [description]

### What Didn't Work

- [description]

### Time Spent

| Phase | Estimated | Actual |
|-------|-----------|--------|
| Extraction | [time] | [time] |
| Mesh Conversion | [time] | [time] |
| Texture Conversion | [time] | [time] |
| CK Assembly | [time] | [time] |
| NPCs & Dialogue | [time] | [time] |
| Packaging | [time] | [time] |
| **Total** | **[time]** | **[time]** |

---

## Copy This Template

For each new city, copy this file and rename it:
```
docs/CITY-[CITYNAME].md
```

Example:
- `docs/CITY-Balmora.md`
- `docs/CITY-Vivec.md`
- `docs/CITY-Aldruhn.md`
- `docs/CITY-Caldera.md`
