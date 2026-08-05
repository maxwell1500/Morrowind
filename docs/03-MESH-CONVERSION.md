# Phase 3: Mesh Conversion Pipeline (NIF to Starfield)

**Estimated Time:** 20-40 hours (depending on mesh complexity)
**Prerequisites:** Phase 2 complete, Blender + Starfield Geometry Bridge installed

## Overview

Convert Morrowind NIF meshes to Starfield-compatible NIF + .mesh files.
This is the most complex and time-consuming phase.

## Understanding the Format Differences

### Morrowind NIF Format
- Version: 4.0.0.2 (NiFile 3.3)
- Geometry is INLINE in the .nif file
- Uses NiTriShape/NiTriStrips for mesh data
- Simple material/texture references
- No separate geometry files

### Starfield NIF Format
- Version: 20.2.0.0+ (NiFile 41.1.0.0+)
- Geometry is SEPARATE in .mesh files (hex path naming)
- Uses BSGeometry for mesh data
- Materials use .mat JSON format
- Morph data in separate morph.dat files
- LoD (Level of Detail) support required

### The Conversion Challenge
You cannot simply open a Morrowind NIF in Starfield's NifSkope. The formats
are fundamentally different. You must:
1. Import the Morrowind NIF into Blender
2. Export it as a Starfield NIF + .mesh
3. Set up materials and collision separately

## Conversion Workflow (Per Mesh)

### Method A: Starfield Geometry Bridge (Recommended for Blender 3.5/3.6)

#### Step 3.1: Import Morrowind NIF

1. Open Blender 3.6
2. File > Import > NetImmerse/Gamebryo (.nif)
   (This option is added by Starfield Geometry Bridge)
3. Navigate to the Morrowind NIF file
4. Import it

**What you'll see:**
- The mesh should appear in Blender's viewport
- UV mapping should be preserved
- Material slots should be visible
- Bone/armature data (if any) should be imported

**Common import issues:**
- Mesh appears inside-out: Normals need flipping (Edit Mode > Mesh > Normals > Recalculate Outside)
- Missing textures: Expected - we'll set these up later
- Weird scaling: Morrowind uses different units than Starfield

#### Step 3.2: Inspect and Clean the Mesh

1. Enter Edit Mode (Tab key)
2. Check for:
   - **Non-manifold edges:** Mesh > Clean Up > Non-Manifold
   - **Duplicate vertices:** Mesh > Clean Up > Merge by Distance
   - **Internal faces:** Delete any faces inside the mesh
   - **Flipped normals:** Mesh > Normals > Recalculate Outside
3. Check UV mapping in UV Editing workspace
4. Verify the mesh looks correct from all angles

**Scale reference:**
- Starfield character height: ~1.8 meters
- Morrowind character height: ~1.8 meters
- Scale should be roughly 1:1, but verify in-game

#### Step 3.3: Prepare for Starfield Export

1. In the Starfield Geometry Bridge panel (N-panel in Blender):
   - Set export path to your `converted_assets/meshes/` folder
   - Choose export settings:
     - Include LoD levels: Yes (generate LoD 1 and 2)
     - Include collision: Yes
     - Material path: Set to match Starfield's material naming convention

2. **Material Path Convention:**
   Starfield expects material paths like:
   ```
   Materials\[Category]\[Name].mat
   ```
   Example: `Materials\Buildings\Imperial\Wall01.mat`

3. **Naming Convention:**
   Name your Blender objects to match the Starfield naming:
   ```
   SEY_ImperialWall01
   SEY_ = Seyda Neen prefix
   ImperialWall01 = descriptive name
   ```

#### Step 3.4: Export as Starfield NIF

1. Select the root object (usually the main mesh)
2. In the Starfield Geometry Bridge panel:
   - Click "Export NIF"
   - This generates:
     - `.nif` file (transform, references, properties)
     - `.mesh` file (geometry data in hex path folder)
     - `morph.dat` (if morphs exist)

3. The .mesh file goes into a hex-pathed folder:
   ```
   converted_assets/meshes/geometries/[hex1]/[hex2]/filename.mesh
   ```
   **Note:** The plugin handles this automatically.

#### Step 3.5: Set Material Paths in NifSkope

1. Open the exported .nif in NifSkope (Starfield fork)
2. Find the BSGeometry node
3. Set the material path to your .mat file
4. Save the .nif

### Method B: NifBlend (For Blender 5.0+)

If using modern Blender, NifBlend offers an alternative:

#### Step 3.1: Install NifBlend

1. Clone or download from github.com/Tzeentchnet/NifBlend
2. Install as Blender extension (Blender 5.0+)
3. Configure Starfield Data root path

#### Step 3.2: Import Morrowind NIF

1. File > Import > NIF (NifBlend)
2. Select the Morrowind NIF file
3. NifBlend handles Morrowind NIF version 4.0.0.2 natively

#### Step 3.3: Export to Starfield

1. File > Export > NIF (NifBlend)
2. Select Starfield as target game
3. Configure export settings

**Note:** NifBlend's Starfield export may be import-only as of current
development. Check the GitHub for latest status.

## Step 3.6: Generate LoD (Level of Detail) Meshes

Starfield requires LoD meshes for performance. For each building mesh:

1. **LoD 0 (Full detail):** The mesh you exported above
2. **LoD 1 (Medium detail):** Simplified version (~50% polygon count)
3. **LoD 2 (Low detail):** Very simplified (~25% polygon count)

**Generation methods:**
- Blender's Decimate modifier (automated simplification)
- Manual retopology (better quality, much more time)
- Starfield Geometry Bridge can auto-generate LoDs

**For Seyda Neen:** Use automated decimation. The buildings are viewed
from relatively close distances, so LoDs don't need to be perfect.

## Step 3.7: Create Collision Data

Starfield meshes need collision data for physics interaction.

**Options:**
1. **Auto-generated:** Starfield Geometry Bridge can create basic collision
2. **Box collision:** Simple bounding box (good for walls, floors)
3. **Mesh collision:** Precise mesh-based collision (good for complex shapes)

**For Seyda Neen buildings:**
- Walls/roofs: Box collision is fine
- Stairs/ramps: Need mesh collision for walkability
- Docks: Mesh collision for the planks

**Setting up collision in NifSkope:**
1. Open the .nif in NifSkope
2. Add BSCompoundCollisionShape or BSMeshCollisionShape
3. Reference the collision mesh
4. Set collision flags appropriately

**Reference:** The Imperial City mod author discovered how to create proper
collisions for all NIF 3D models. This was a major breakthrough documented
in Magnus update 4.8.

## Step 3.8: Batch Conversion Script

For converting multiple meshes, create a batch script:

```python
#!/usr/bin/env python3
"""
batch_convert_morrowind_meshes.py

Batch converts Morrowind NIF files to Starfield format.
Requires Blender 3.6 with Starfield Geometry Bridge.

Usage:
  blender --background --python batch_convert_morrowind_meshes.py -- [input_dir] [output_dir]
"""

import bpy
import os
import sys
import glob

# Get arguments after --
argv = sys.argv[sys.argv.index("--") + 1:]
input_dir = argv[0] if len(argv) > 0 else "raw_assets/seyda_neen/meshes"
output_dir = argv[1] if len(argv) > 1 else "converted_assets/meshes"

# Find all NIF files
nif_files = glob.glob(os.path.join(input_dir, "*.nif"))

for nif_path in nif_files:
    filename = os.path.basename(nif_path)
    print(f"Converting: {filename}")

    # Clear scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import NIF
    try:
        bpy.ops.import_scene.nif(filepath=nif_path)
    except Exception as e:
        print(f"  ERROR importing {filename}: {e}")
        continue

    # Set up export path
    export_path = os.path.join(output_dir, filename)

    # Export as Starfield NIF
    try:
        bpy.ops.export_scene.nif(filepath=export_path)
        print(f"  Exported: {export_path}")
    except Exception as e:
        print(f"  ERROR exporting {filename}: {e}")
        continue

print("Batch conversion complete.")
```

**Run with:**
```batch
blender --background --python scripts\batch_convert_morrowind_meshes.py -- ^
  "raw_assets\seyda_neen\meshes" ^
  "converted_assets\meshes"
```

## Step 3.9: Quality Checklist (Per Mesh)

Before considering a mesh "done," verify:

- [ ] Mesh imports into Blender without errors
- [ ] UV mapping is intact (textures align correctly)
- [ ] Normals face outward (no black faces)
- [ ] Mesh is clean (no non-manifold edges, duplicate vertices)
- [ ] Scale matches Starfield character height
- [ ] Export produces both .nif and .mesh files
- [ ] Material path is set correctly in NifSkope
- [ ] Collision data is present
- [ ] LoD meshes are generated (at least LoD 1)
- [ ] Mesh loads in Starfield CK without errors
- [ ] Mesh appears correctly in-game

## Step 3.10: Common Conversion Issues

### "Mesh appears black in-game"
- **Cause:** Missing or incorrect material path
- **Fix:** Set material path in NifSkope to a valid .mat file

### "Mesh is invisible"
- **Cause:** Backface culling + flipped normals
- **Fix:** Recalculate normals in Blender, ensure front faces face outward

### "Mesh has no collision"
- **Cause:** Missing collision data in .nif
- **Fix:** Add collision shape in NifSkope

### "Mesh is the wrong size"
- **Cause:** Scale mismatch between Morrowind and Starfield
- **Fix:** Scale in Blender before export (Morrowind ~1:1 with Starfield)

### "UV mapping is scrambled"
- **Cause:** UV channels don't match Starfield expectations
- **Fix:** Re-UV map in Blender using the original as reference

### "Mesh won't import into CK"
- **Cause:** Incorrect .nif version or missing .mesh
- **Fix:** Ensure both .nif and .mesh are in correct paths

## Conversion Priority Order

Convert in this order for maximum learning and minimum frustration:

1. **Simple wall** (`in_c_brick_wall.nif`) - Test basic pipeline
2. **Flat floor** (`in_c_floor.nif`) - Verify UV and materials
3. **Simple building** (one complete house) - Full pipeline test
4. **Dock pieces** - Test larger structures
5. **Lighthouse** - Iconic, more complex
6. **Remaining buildings** - Batch process
7. **Furniture** - Smaller, simpler
8. **Clutter** - Last priority

## Estimated Mesh Count for Seyda Neen

| Category | Count | Complexity |
|----------|-------|------------|
| Imperial walls | 5-8 | Simple |
| Imperial floors/ceilings | 3-5 | Simple |
| Roofs | 3-5 | Medium |
| Windows/doors | 3-5 | Simple |
| Stairs/ramps | 2-3 | Medium |
| Dock pieces | 3-5 | Medium |
| Lighthouse | 1 | Medium-High |
| Dunmer buildings | 3-5 | Medium |
| Furniture | 10-15 | Simple |
| Clutter | 15-20 | Simple |
| **Total** | **~50-75** | |

This is very manageable compared to a full city conversion.

## Checklist

- [ ] Test conversion pipeline on one simple mesh
- [ ] Verify material path convention
- [ ] Verify collision creation workflow
- [ ] Convert all high-priority meshes
- [ ] Convert all medium-priority meshes
- [ ] Generate LoD meshes
- [ ] Create collision for all meshes
- [ ] Quality check each converted mesh
- [ ] Document any issues/solutions in LESSONS-LEARNED.md

## Next Phase

Proceed to [Phase 4: Texture Conversion](04-TEXTURE-CONVERSION.md) to
upscale and convert Morrowind textures for Starfield.
