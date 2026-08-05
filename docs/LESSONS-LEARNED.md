# Lessons Learned

**Purpose:** Running log of discoveries, solutions, and gotchas encountered
during the project. Referenced by future city conversions.

*Add entries chronologically. Format: Date - Category - Description*

---

## Tool Setup

### Blender Version

**Date:** TBD
**Category:** Tool Setup
**Issue:** Starfield Geometry Bridge doesn't work with Blender 4.0+
**Solution:** Use Blender 3.5 or 3.6 specifically. Or use NifBlend for 5.0+.
**Impact:** Low - just use the right version

### NifSkope Version

**Date:** TBD
**Category:** Tool Setup
**Issue:** Standard NifSkope doesn't support Morrowind or Starfield NIF versions
**Solution:** Use the fo76utils fork of NifSkope for Starfield
**Impact:** Medium - wrong NifSkope causes confusion

---

## Asset Extraction

### BSA Structure

**Date:** TBD
**Category:** Extraction
**Discovery:** Morrowind BSA files have a simpler structure than Starfield BA2
**Details:** Morrowind uses hash-based file lookup; Starfield uses path-based
**Impact:** Low - BAE handles both transparently

### Texture Formats

**Date:** TBD
**Category:** Extraction
**Discovery:** Some Morrowind textures are TGA, not DDS
**Solution:** Convert TGA to DDS before upscaling (GIMP or batch script)
**Impact:** Low - extra step but straightforward

---

## Mesh Conversion

### NIF Version Gap

**Date:** TBD
**Category:** Mesh Conversion
**Discovery:** Morrowind NIF 4.0.0.2 and Starfield NIF 20.2.0.0+ are
fundamentally different formats, not just version bumps
**Details:** Geometry is inline in Morrowind, separate .mesh in Starfield
**Impact:** High - cannot simply "upgrade" NIF version, must go through Blender

### Geometry Bridge Workflow

**Date:** TBD
**Category:** Mesh Conversion
**Discovery:** Starfield Geometry Bridge exports .nif AND .mesh in one operation
**Details:** The .mesh goes into a hex-pathed folder automatically
**Impact:** Medium - must keep .nif and .mesh together

### Material Paths

**Date:** TBD
**Category:** Mesh Conversion
**Discovery:** Material paths in Starfield NIFs use backslash separators
**Details:** Example: `Materials\Buildings\Wall01.mat` not forward slash
**Impact:** Medium - wrong path = black textures

### Collision Creation

**Date:** TBD
**Category:** Mesh Conversion
**Discovery:** Collision must be added separately, not embedded in mesh
**Details:** Use NifSkope to add BSCompoundCollisionShape
**Impact:** High - no collision = walk through walls

### Scale

**Date:** TBD
**Category:** Mesh Conversion
**Discovery:** Morrowind and Starfield use similar character height (~1.8m)
**Details:** Scale should be roughly 1:1, verify in-game
**Impact:** Low - no major scaling needed

---

## Texture Conversion

### AI Upscaling Artifacts

**Date:** TBD
**Category:** Texture Conversion
**Discovery:** ESRGAN can produce streaky lines on some textures
**Solution:** Use RealESRGAN_x4plus_anime_6B for stylized game art
**Impact:** Medium - affects visual quality

### Tiling Textures

**Date:** TBD
**Category:** Texture Conversion
**Discovery:** AI upscaling breaks tiling at texture edges
**Solution:** Extend texture edges before upscaling, or fix seams manually
**Impact:** Medium - visible seams if not addressed

### Color Shift

**Date:** TBD
**Category:** Texture Conversion
**Discovery:** AI models shift colors slightly during upscaling
**Solution:** Apply color correction post-upscale (match original)
**Impact:** Low - easy fix with GIMP

---

## Creation Kit

### CK Load Time

**Date:** TBD
**Category:** Creation Kit
**Discovery:** CK takes 4+ minutes to load, especially with Magnus
**Solution:** Be patient, save frequently, don't close/reopen unnecessarily
**Impact:** Medium - workflow disruption

### Memory Usage

**Date:** TBD
**Category:** Creation Kit
**Discovery:** CK uses 15-32GB RAM with large mods loaded
**Solution:** Close all other applications, use 32GB+ RAM system
**Impact:** High - can crash if insufficient memory

### Cell Navigation

**Date:** TBD
**Category:** Creation Kit
**Discovery:** Exterior cell navigation in CK is clunky
**Solution:** Use 'A' for lighting toggle, 'T' to center on selection
**Impact:** Low - learning curve

---

## Integration

### Load Order

**Date:** TBD
**Category:** Integration
**Discovery:** Our mod must load AFTER Magnus in load order
**Solution:** Set Magnus as master in our plugin
**Impact:** High - wrong order = missing references

### Coordinate Alignment

**Date:** TBD
**Category:** Integration
**Discovery:** Need to determine exact coordinates for Seyda Neen on Magnus
**Solution:** Scout in-game or check with Magnus community
**Impact:** High - wrong coordinates = town in wrong location

---

## General

### Time Estimates

**Date:** TBD
**Category:** General
**Discovery:** Asset conversion takes much longer than expected
**Details:** Imperial City took 137+ hours; Seyda Neen estimated 70-120 hours
**Impact:** High - plan for significant time investment

### Documentation Value

**Date:** TBD
**Category:** General
**Discovery:** Documenting every step saves enormous time on future cities
**Solution:** Keep this log updated, reference CITY-TEMPLATE.md
**Impact:** High - multiplied value across all future cities

---

*Add new entries above this line, newest first*
