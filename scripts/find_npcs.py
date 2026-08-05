import json
with open(r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind.json", "r", encoding="utf-8") as f:
    data = json.load(f)

npcs = [o for o in data if o.get("type") == "NPC_"]
print("NPC records:", len(npcs))
for n in npcs[:5]:
    print("  ID:", n.get("id"), " Name:", n.get("name"))

seyda_cells = [o for o in data if o.get("type") == "Cell" and "seyda" in o.get("name", "").lower()]
all_ref_ids = set()
for cell in seyda_cells:
    for ref in cell.get("references", []):
        all_ref_ids.add(ref.get("id", "").lower())

npc_ids = {o.get("id", "").lower(): o.get("name", "") for o in npcs}
found_npcs = {rid: npc_ids[rid] for rid in all_ref_ids if rid in npc_ids}
print("\nNPCs found in Seyda Neen refs:", len(found_npcs))
for rid, name in sorted(found_npcs.items()):
    print(" ", rid, "->", name)

# Also look at "owner" and "owner_faction" fields in Seyda Neen refs
print("\nLooking at owner fields:")
for cell in seyda_cells:
    for ref in cell.get("references", []):
        owner = ref.get("owner", "")
        faction = ref.get("owner_faction", "")
        if owner or faction:
            print(f"  {ref.get('id')} -> owner={owner} faction={faction}")
