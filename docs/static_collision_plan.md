# Static Collision Plan (Option A: hknpCompressedMeshShape)

## Findings from native static (Starborn_BuiltInKitchenette01.nif)

### Block structure
- bhkNPCollisionObject: `00000000 8000 0300 00000000 0000` (target=0, flags=0x0080, phys_ref=3, body_id=0)
- BSXFlags: 0x00000002 (static Havok)
- bhkPhysicsSystem: 9548B, data_len=9544

### TAG0 tree (20 items)
```
TAG0
├── SDKV (16B)
├── DATA (2440B body)
├── TYPE (6608B - TYPE table verbatim, can be copied)
│   ├── TPTR, TST1, TNA1, FST1, TBDY, THSH, TPAD
└── INDX (472B)
    ├── ITEM (248B - 20 items)
    └── PTCH (216B - 17 patches)
```

### Item layout (20 items)
| idx | type                    | data_off | count | size/notes |
|-----|-------------------------|----------|-------|------------|
| 0   | hknpPhysicsSystemData  | 0x0      | 0     | null/base  |
| 1   | PhysicsSystemData      | 0x0      | 1     | 112B       |
| 2   | hknpMaterial            | 0x70     | 1     | 80B        |
| 3   | bodyCinfo               | 0xc0     | 1     | 192B (ref to shape=4) |
| 4   | hknpCompressedMeshShape | 0x180    | 1     | 128B       |
| 5   | RefCountedProperties    | 0x208    | 1     | 56B (properties) |
| 6   | CompressedMeshShapeData| 0x240    | 1     | 264B       |
| 7   | hkUint32               | 0x200    | 2     | 8B         |
| 8   | RefCountedProperties::Entry | 0x230 | 1 | 16B |
| 9   | hknpBSMaterialProperties| 0x930   | 1     | 32B        |
| 10  | Aabb5BytesCodec         | 0x350    | 1     | 8B         |
| 11  | Section                 | 0x360    | 1     | 96B (section header) |
| 12  | Primitive               | 0x3c0    | 18    | 18×8B=144B (triangles) |
| 13  | hkUint16               | 0x410    | 6     | 12B (sharedVerticesIndex?) |
| 14  | unsigned int           | 0x420    | 14    | 56B (primitives?) |
| 15  | unsigned long long     | 0x460    | 6     | 48B (primitives?) |
| 16  | PrimitiveDataRun       | 0x490    | 1     | 8B         |
| 17  | SimdTree::Node         | 0x4a0    | 8     | 8×128B=1024B |
| 18  | Aabb4BytesCodec        | 0x8a0    | 35    | 35×6B=210B |
| 19  | hknpBSMaterial         | 0x960    | 1     | 32B        |

### Body CInfo (item 3, the actual rigid body)
At 0xc0, 192 bytes. Key fields:
- offset 0xc0: shape=4 (hkRefPtr to CompressedMeshShape)
- offset 0xc8: flags=0
- offset 0xe8: motionType=0 (STATIC)
- offset 0xf0: position=(0,0,0)
- offset 0x100: orientation=(0,0,0,1) identity quaternion at 0x108
- All zero elsewhere (no mass, no velocity)

### Section (item 11, 96 bytes)
- Contains AABB domain, codec params, counts:
  - numPackedVertices (byte 88)
  - numPrimitives (byte 89)
  - numDataRuns (byte 90)
- firstPackedVertexIndex, firstSharedVertexIndex, firstPrimitiveIndex, firstDataRunIndex

### Primitives (item 12, 18 triangles)
Each triangle is 8 bytes (3 vertex indices + padding). Vertex indices reference packedVertices.

### SimdTree (item 17, 8 nodes × 128B)
AABB tree. Internal nodes have 4 child AABBs; leaf nodes point to primitives.

### Aabb4BytesCodec (item 18, 35 nodes × 6B)
Compressed AABB tree for the static mesh tree.

## Approach (Plan A.1 — Verbatim clone, fixed geometry)

**Step 1**: Clone kitchenette's entire bhkPhysicsSystem block verbatim into Morrowind NIFs. This gives every mesh an 18-triangle static collision shape that doesn't match the mesh — but it IS a valid static Havok body. The 18 triangles are small (the kitchenette is ~1.5m wide), so collision will be roughly box-sized around origin.

**Step 2**: Test in CK with full 434-exterior-REFR ESP. Should NOT hang (static bodies are cheap). Verify no crash.

**Step 3**: Test in-game. Walking on objects won't be precise but should confirm the approach works.

If Plan A.1 succeeds, we know the static physics system structure is correct. Then:

## Approach (Plan A.2 — Per-mesh geometry, two strategies)

**Strategy 1: Single-triangle plane** — Replace the 18 triangles with 1 degenerate or small triangle per mesh. Even simpler than verbatim.

**Strategy 2: AABB box as compressed mesh** — Build a 12-triangle box from each mesh's AABB and encode into the compressed mesh format. This gives proper box collision matching each mesh.

**Strategy 3: Full per-mesh triangles** — Encode all triangles from the mesh. Most accurate but complex encoder needed.

I'll start with Plan A.1 (verbatim clone) to validate, then move to Strategy 2 (AABB box as compressed mesh) for actual collision.

## Critical fix vs old clone_collision.py

The old script cloned the **crate** (dynamic, convex hull). The new script must:
1. Use kitchenette as donor (static, compressed mesh)
2. NOT modify bhkNPCollisionObject flags (they're already 0x0080 in the donor — clone verbatim, only patch target_ref and phys_ref)
3. Keep BSXFlags=0x02 (already correct)
4. The kitchenette's bhkPhysicsSystem is 9548B vs crate's 6172B — bigger but still fine

## File plan

1. `clone_static.py` — clone kitchenette's static Havok blocks into Morrowind NIFs (verbatim physics system)
2. Test with full ESP in CK
3. If works, write `encode_compressed_mesh.py` — build per-mesh AABB box as compressed mesh tree, replace DATA+INDX of cloned physics system
4. Re-inject per-mesh, test again