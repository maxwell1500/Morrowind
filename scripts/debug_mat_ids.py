import os, json
mat_dir = r'C:\Users\max\Projects\Morrowind\Data\Materials\morrowind'
files = sorted(os.listdir(mat_dir))
ids_by_file = {}
for fname in files:
    path = os.path.join(mat_dir, fname)
    with open(path) as f:
        data = json.load(f)
    ids = []
    for obj in data['Objects']:
        if 'ID' in obj:
            ids.append(obj['ID'])
    ids_by_file[fname] = ids
    print(f"{fname}: first ID={ids[0] if ids else 'NONE'}")

# Check for duplicate full IDs
seen = {}
for fname, ids in ids_by_file.items():
    for id_ in ids:
        seen.setdefault(id_, []).append(fname)

print("\n=== DUPLICATE IDs ===")
dupes = [(id_, files) for id_, files in seen.items() if len(files) > 1]
print(f"Total duplicate IDs: {len(dupes)}")
for id_, files in dupes[:10]:
    print(f"  {id_}: {files}")
if len(dupes) > 10:
    print(f"  ... and {len(dupes)-10} more")
