import sys
sys.path.append(r'C:\Users\max\Projects\Morrowind\tools\SGB\tool_export_mesh')
import NifIO
import json

# Import the dock NIF as JSON
nif_data = NifIO.ImportNifAsJson(r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif')
print('NIF data keys:', list(nif_data.keys()))
print('Number of blocks:', len(nif_data.get('blocks', [])))

# Find bhkNP blocks
for i, block in enumerate(nif_data.get('blocks', [])):
    name = block.get('name', '')
    if 'bhkNP' in name or 'bhk' in name:
        print()
        print('Block', i, ':', name)
        print('  Data:', json.dumps(block, indent=2)[:500])
