import json
with open(r'C:\Users\max\Projects\Morrowind\converted_assets\mapping\morrowind_mesh_bounds.json') as f:
    bounds = json.load(f)
sized = []
for name, b in bounds.items():
    mn, mx = b['min'], b['max']
    extent = max(mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2])
    sized.append((extent, name, b))
sized.sort(reverse=True)
print('Top 15 largest meshes:')
for ext, name, b in sized[:15]:
    print(f'  {name:40s} max_extent={ext:6.2f}')
print('\nTop 15 smallest meshes:')
for ext, name, b in sized[-15:]:
    print(f'  {name:40s} max_extent={ext:6.4f}')
