import os
import sys

mesh_dir = r"C:\Users\max\Projects\Morrowind\converted_assets\meshes"
files = sorted([f for f in os.listdir(mesh_dir) if f.endswith('.nif')])[:5]

for f in files:
    path = os.path.join(mesh_dir, f)
    with open(path, 'rb') as fh:
        data = fh.read()
    # Find texture-related strings
    strings = []
    i = 0
    while i < len(data) - 4:
        if data[i] == 0 and i > 0 and data[i-1] != 0:
            end = i
            start = end - 1
            while start > 0 and data[start-1] != 0:
                start -= 1
            s = data[start:end].decode('ascii', errors='ignore')
            if len(s) > 3 and ('/' in s or '\\' in s or '.' in s):
                strings.append(s)
        i += 1
    unique = sorted(set(strings))
    print(f"\n{f}:")
    for s in unique[:20]:
        print(f"  {s}")
