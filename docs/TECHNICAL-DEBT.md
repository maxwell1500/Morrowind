# Technical Debt & Deferred Work

**Purpose:** A living register of known problems, shortcuts, and unfinished features that are intentionally parked. This keeps the main tracker clean while preserving context for future work.

**Last Updated:** 2026-07-09
**Status:** Active — collision work parked, shifting to broader world-building tasks.

---

## How to Use This Document

- **Before starting new work:** Check this list so you don't re-discover old dead-ends.
- **When parking an issue:** Add it here with a clear "Future path" and "Revisit condition".
- **When resuming an issue:** Move the relevant entry to the active todo list and update this doc when resolved.
- **When closing an issue:** Move it to the **Resolved / Retired** section at the bottom with a brief note.

---

## Active Technical Debt

### Collision

#### 1. Stair / dock ramp collision is not walkable

- **What we tried:**
  - `hknpBoxShape` donor from `Starborn_CrewChest01.nif`, scaled to each mesh AABB, with body orientation rotated for stairs.
  - `hknpConvexShape` ramp donor from `Starborn_ShipModelPedestal01.nif`, replacing hull vertices/planes with a right-triangular prism.
- **Result:** CK collision wireframe still appears as a vertical box. In-game walking up stairs requires jumping.
- **Root cause (tentative):** Static collision bodies in Starfield appear to use an axis-aligned bounding box or ignore body/shape orientation for static queries. The convex hull replacement either is not parsed by Starfield or is being re-fitted to an AABB.
- **Current mitigation:** Reverted the three stair meshes to the standard `clone_box.py` box collision. They are solid but not ramps.
- **Future path:**
  - Find a native Starfield static object that CK displays as a visibly sloped or non-box collision wireframe and use it as a donor.
  - Build a real `hknpCompressedMeshShape` or `hknpConvexShape` encoder rather than trying to patch donor hulls.
- **Revisit condition:** Player feedback shows stairs/docks are a blocker, OR a sloped static donor is identified.
- **Files:** `scripts/collision/clone_box.py`, `scripts/collision/clone_convex_ramp.py`, `scripts/collision/build_convex_hull.py`.

#### 2. Collision is per-mesh AABB box, not shape-accurate

- **What we tried:** `Starborn_BuiltInKitchenette01.nif` compressed-mesh donor with full Aabb4/Aabb5 tree. Replacing its vertices/primitives without rebuilding the tree produced mangled flat planes in CK.
- **Result:** All 238 meshed STATs use `hknpBoxShape` from `Starborn_CrewChest01.nif`, scaled to AABB. Collision is roughly correct in size but is always a box.
- **Current mitigation:** Box collision is good enough for walking around buildings and most props.
- **Future path:**
  - Write a real `hknpCompressedMeshShape` generator from mesh triangles, including the Aabb4/Aabb5 codec tree.
  - Or find a native static that uses a simpler triangle-mesh or convex shape and clone its topology.
- **Revisit condition:** After all cities are placed and basic gameplay works.
- **Files:** `docs/static_collision_plan.md`, `scripts/collision/encode_static_box.py`.

#### 3. Four meshes have no collision

- **What happened:** `scripts/compute_mw_bounds.py` skipped 4 meshes when building `converted_assets/mapping/morrowind_mesh_bounds.json` (Blender import issues).
- **Result:** Those 4 STATs have no `bhkNPCollisionObject` / `bhkPhysicsSystem` blocks.
- **Current mitigation:** None.
- **Future path:** Add manual bounds entries to `morrowind_mesh_bounds.json`, then re-run `clone_box.py`.
- **Revisit condition:** Before any public release.

---

### World Integration

#### 4. No door teleportation between interiors and exteriors

- **What we know:** Starfield doors use a different teleport format than Morrowind. We have not yet decoded the exact `DOOR` / `REFR` subrecords that store destination cell + position.
- **Result:** Interiors are disconnected from the exterior worldspace. Player can walk into an interior cell only via CK or console, not through a working door.
- **Current mitigation:** Interiors exist as isolated cells.
- **Future path:** Decode door teleport records from `ImperialCity.esm` or a working Starfield mod. Add `DOOR` STATs and linked `REFR`s to the ESP generator.
- **Revisit condition:** Before declaring Seyda Neen "playable".
- **Files:** `scripts/generate_full_seydaneen.py`, `docs/08-ESP-BINARY-FORMAT.md`.

#### 5. Terrain is flat Magnus placeholder ground

- **What we know:** Magnus's Morrowind province has flat landing zones intentionally left blank for modders. We currently place objects directly on that flat terrain with a `Z_OFFSET` of ~480.
- **Result:** Seyda Neen floats on a flat plain; no Bitter Coast hills, no natural ground contour.
- **Current mitigation:** None.
- **Future path:**
  - **Option A (CK):** Create a worldspace overlay in CK, sculpt terrain, export landscape data, and include it in the plugin.
  - **Option B (platforms):** Build wooden/stone foundation platforms under Seyda Neen so the flat ground is hidden.
- **Revisit condition:** Once basic collision and doors are working.

#### 6. Water is disabled (XCLW = FLT_MAX)

- **What we know:** Setting `XCLW` to `0.0` creates a water plane at z=0 that covers everything. Setting it to `FLT_MAX` disables water.
- **Result:** No Bitter Coast water around docks or swamps.
- **Current mitigation:** No water.
- **Future path:** Determine the correct water subrecord values (water type, height, image space) for a Bitter Coast cell by comparing to a working Starfield coastal cell, then set it in the generator.
- **Revisit condition:** After terrain decision is made.

---

### Content

#### 7. No NPCs, creatures, or dialogue

- **What we know:** We have not created `NPC_`, `CREA`, `DIAL`, `PACK`, `OUTF`, `ARMO`, `CLOTH`, or facegen records. Clothing/armor meshes are not converted.
- **Result:** Seyda Neen is an empty ghost town.
- **Current mitigation:** None.
- **Future path:**
  - Convert a small set of essential clothing NIFs.
  - Create ~10–15 NPCs in CK using Starfield templates + converted outfits.
  - Write minimal greetings/services dialogue.
  - Add AI packages (idle, sand, sleep, work).
- **Revisit condition:** After world collision and doors are stable.
- **Files:** `docs/06-NPCS-CREATURES.md`.

#### 8. No ambient sound or music

- **What we know:** Morrowind ambient sounds and music are not extracted or placed.
- **Result:** Location is silent.
- **Current mitigation:** None.
- **Future path:** Extract Morrowind audio, convert to Starfield formats if needed, and place ambient sound markers in CK.
- **Revisit condition:** After NPC pass.

---

### Performance & Polish

#### 9. No LOD meshes

- **What we know:** We have not generated LoD NIFs for any converted meshes.
- **Result:** Buildings may pop in at distance; performance may suffer with many unique high-poly meshes.
- **Current mitigation:** None.
- **Future path:** Generate LoD meshes via Blender decimation or CK's built-in LoD tools, then reference them in the STAT records.
- **Revisit condition:** Before any performance testing.

#### 10. No navmesh

- **What we know:** CK can bake navmesh once collision and terrain are final.
- **Result:** NPCs and creatures cannot pathfind.
- **Current mitigation:** None.
- **Future path:** Bake navmesh in CK for each interior and the exterior cell.
- **Revisit condition:** After collision and terrain are final.

#### 11. Many interior cell warnings in CK

- **What we know:** CK reports "improperly positioned interior cell" and "Potentially Invalid X/Y value" warnings.
- **Result:** Warnings are cosmetic; interiors load. But they may hide real issues.
- **Current mitigation:** Documented as cosmetic in `AGENTS.md`.
- **Future path:** Investigate whether interior REFR coordinates should be local-to-cell vs. world-relative, and whether interior cell block/subblock indices need adjustment.
- **Revisit condition:** If interiors stop loading or NPC pathing breaks.

---

## Resolved / Retired

| Item | Resolution | Date |
|---|---|---|
| NIF material paths defaulting to `MATERIAL_PATH` | Fixed by creating Blender material before SGB export | 2026-07-03 |
| `.mat` files causing magenta / "has no layer" | Fixed by cloning full Starborn material structure with valid CDB IDs | 2026-07-03 |
| Old SGB Havok blocks corrupting NIFs | Fixed by stripping `bhkConvexVerticesShape`, `bhkCollisionObject`, `bhkRigidBody` before injection | 2026-07-06 |
| Cell `DATA` flag and `XCLW` water height | Fixed to `0x00000202` and `FLT_MAX` respectively | 2026-07-02 |
| Coordinate scale bug (8192 vs 100 cells) | Fixed by scaling coordinates by `100/8192` | 2026-07-02 |
| FormID collision between LCTN and STAT | Fixed by starting STATs at `0xFE000100` | 2026-07-02 |

---

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-09 | Keep box collision; park stair ramp work | User wants to move on to broader world-building; convex ramp donor did not produce visible ramp in CK. |
| 2026-07-09 | Create this technical-debt document | Keep `AGENTS.md` focused on current status; avoid losing context on abandoned approaches. |

---

## Next Review

Review this document whenever:
- A milestone is completed and new debt is discovered.
- A previously parked item becomes blocking.
- A month has passed without an update.
