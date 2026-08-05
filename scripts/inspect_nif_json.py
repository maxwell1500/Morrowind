import sys
import json

sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
from MeshConverter import ImportNifAsJson

nif_path = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes\ex_de_sn_gate.nif"
nif_json = ImportNifAsJson(nif_path, False, "")
nif_data = json.loads(nif_json)

# Find BSGeometry nodes
def find_nodes(obj, node_type, results):
    if isinstance(obj, dict):
        t = obj.get("type", "")
        if node_type in t:
            results.append(obj)
        for v in obj.values():
            find_nodes(v, node_type, results)
    elif isinstance(obj, list):
        for item in obj:
            find_nodes(item, node_type, results)

bs_geom = []
find_nodes(nif_data, "BSGeometry", bs_geom)
print(f"Found {len(bs_geom)} BSGeometry nodes")

if bs_geom:
    node = bs_geom[0]
    print(f"Keys: {list(node.keys())}")
    for k in ["type", "name", "mat_path", "materialPath", "material"]:
        if k in node:
            print(f"  {k}: {node[k]}")
    if "extraData" in node:
        ed_count = len(node["extraData"])
        print(f"  extraData ({ed_count}):")
        for ed in node["extraData"]:
            name = ed.get("name", "?")
            sdata = ed.get("stringData", "?")
            print(f"    {name}: {sdata}")
    # Show full first node
    print("\nFull first BSGeometry node:")
    print(json.dumps(node, indent=2)[:2000])
