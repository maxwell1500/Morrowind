with open(r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif', 'rb') as f:
    data = f.read()

# Search for bhkNP or bhkR
for marker in [b'bhkNP', b'bhkR', b'bhkC']:
    marker_name = marker.decode()
    idx = data.find(marker)
    if idx >= 0:
        print(f'Found "{marker_name}" at offset {idx}')
        # Print context
        print(f'  Context: {data[idx-10:idx+30].hex()}')
    else:
        print(f'"{marker_name}" not found')

# Print full block type string table
print('\nBlock type string table:')
pos = 64
while pos < len(data) - 4:
    length = struct.unpack_from('<I', data, pos)[0]
    if length > 100 or length < 1 or pos + 4 + length > len(data):
        break
    s = data[pos+4:pos+4+length]
    try:
        s.decode('ascii')
        print(f'  {s.decode("ascii")}')
        pos += 4 + length
        pos = (pos + 3) & ~3
    except:
        break
