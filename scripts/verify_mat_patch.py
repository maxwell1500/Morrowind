import sys
import json

sys.path.insert(0, r"C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh")
from MeshConverter import ImportNifAsJson

nif_path = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes\ex_de_sn_gate.nif"
nif_json = ImportNifAsJson(nif_path, False, "")
nif_data = json.loads(nif_json)
for geo in nif_data.get("geometries", []):
    print(f"  mat_path: {geo.get('mat_path', 'MISSING')}")
    break
