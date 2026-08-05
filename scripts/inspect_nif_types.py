import sys
import json

sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
from MeshConverter import ImportNifAsJson

nif_path = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes\ex_de_sn_gate.nif"
nif_json = ImportNifAsJson(nif_path, False, "")
nif_data = json.loads(nif_json)

# Show all node types
def collect_types(obj, types_set):
    if isinstance(obj, dict):
        t = obj.get("type", "")
        if t:
            types_set.add(t)
        for v in obj.values():
            collect_types(v, types_set)
    elif isinstance(obj, list):
        for item in obj:
            collect_types(item, types_set)

types = set()
collect_types(nif_data, types)
print("Node types found:")
for t in sorted(types):
    print(f"  {t}")

# Find all objects with mat_path or material references
def find_material_refs(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "mat" in k.lower() or "material" in k.lower():
                print(f"  {path}.{k} = {v}")
            find_material_refs(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_material_refs(item, f"{path}[{i}]")

print("\nMaterial-related fields:")
find_material_refs(nif_data)
