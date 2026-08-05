"""
Extract Seyda Neen asset list from Morrowind.esm JSON
Finds all cells and objects in Seyda Neen.
"""
import json
import sys
from collections import Counter

def main():
    print("Loading Morrowind.esm JSON...")
    with open(r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} records")
    
    # Find all Seyda Neen cells (interior and exterior)
    seyda_cells = []
    for obj in data:
        if obj.get("type") == "Cell":
            name = obj.get("name", "")
            if "seyda" in name.lower():
                seyda_cells.append(obj)
    
    print(f"\nFound {len(seyda_cells)} Seyda Neen cells:")
    for cell in seyda_cells:
        refs = cell.get("references", [])
        print(f"  {cell['name']} ({len(refs)} references)")
    
    # Also find the exterior cell (Seyda Neen is in grid -2, -9 approximately)
    # The exterior cells don't have "Seyda Neen" in the name, they use grid coords
    # Let's find cells that reference Seyda Neen objects
    
    # Extract all unique object IDs from Seyda Neen cells
    all_objects = []
    for cell in seyda_cells:
        for ref in cell.get("references", []):
            obj_id = ref.get("id", "")
            all_objects.append(obj_id)
    
    # Count occurrences
    obj_counts = Counter(all_objects)
    
    # Categorize objects
    categories = {
        "meshes": [],      # NIF files (buildings, furniture, etc.)
        "npcs": [],        # NPC IDs
        "creatures": [],   # Creature IDs
        "items": [],       # Item IDs
        "other": []
    }
    
    # Known NPC/creature prefixes
    npc_names = set()
    creature_names = set()
    
    # Get all NPC records
    npc_records = {obj.get("id", "").lower(): obj for obj in data if obj.get("type") == "NPC_"}
    
    # Get all creature records
    creature_records = {obj.get("id", "").lower(): obj for obj in data if obj.get("type") == "Creature"}
    
    # Classify objects
    for obj_id, count in obj_counts.most_common():
        obj_lower = obj_id.lower()
        
        # Check if it's an NPC
        if obj_lower in npc_records:
            categories["npcs"].append((obj_id, count))
        # Check if it's a creature
        elif obj_lower in creature_records:
            categories["creatures"].append((obj_id, count))
        # Check if it's a mesh (starts with known prefixes)
        elif any(obj_lower.startswith(p) for p in ["in_", "ex_", "furn_", "com_", "misc_", "light_", "active_", "door_", "de_", "imp_", "nor_", "bm_"]):
            categories["meshes"].append((obj_id, count))
        # Check if it's an item
        elif any(obj_lower.startswith(p) for p in ["armor_", "weap_", "cloth_", "book_", "ingred_", "alchemy_", "pro_potion_"]):
            categories["items"].append((obj_id, count))
        else:
            categories["other"].append((obj_id, count))
    
    # Print results
    print("\n" + "="*60)
    print("SEYDA NEEN ASSET INVENTORY")
    print("="*60)
    
    for category, items in categories.items():
        if items:
            print(f"\n--- {category.upper()} ({len(items)} unique) ---")
            for obj_id, count in sorted(items, key=lambda x: -x[1])[:50]:
                print(f"  {obj_id} (x{count})")
    
    # Save full list to file
    output = {
        "cells": [{"name": c["name"], "refs": len(c.get("references", []))} for c in seyda_cells],
        "objects": {obj_id: count for obj_id, count in obj_counts.most_common()},
        "categories": {k: [(id, c) for id, c in v] for k, v in categories.items()}
    }
    
    with open(r"C:\Users\max\Projects\Morrowind\raw_assets\seyda_neen_inventory.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nFull inventory saved to seyda_neen_inventory.json")
    print(f"\nTotal unique objects: {len(obj_counts)}")
    print(f"Total references: {sum(obj_counts.values())}")

if __name__ == "__main__":
    main()
