import struct, zlib, csv, math
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
grids = {}
refr_count = 0
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig == b'CELL':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        body = data[pos+24:pos+24+size]
        if flags & 0x00040000:
            body = zlib.decompress(body[4:])
        sub = 0
        xclc = None
        edid = None
        while sub < len(body):
            ssig = body[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            sdata = body[sub+6:sub+6+sln]
            if ssig == 'XCLC':
                xclc = struct.unpack('<iii', sdata)
            elif ssig == 'EDID':
                edid = sdata.rstrip(b'\x00').decode('ascii', errors='replace')
            sub += 6 + sln
        if xclc:
            grids[xclc[:2]] = (formid, edid)
        pos += 24 + size
    elif sig == b'GRUP':
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 24 + struct.unpack('<I', data[pos+4:pos+8])[0]
print('Exterior CELL grids in ESP:')
for k, v in sorted(grids.items()):
    print(f'  {k}: fid=0x{v[0]:08X} edid={v[1]}')

# Check relative coords
minx = miny = float('inf')
maxx = maxy = float('-inf')
with open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv', newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['cell'].strip() != 'Seyda Neen':
            continue
        x = float(row['x_mw']); y = float(row['y_mw'])
        gx = int(math.floor(x / 8192)); gy = int(math.floor(y / 8192))
        rx = (x - gx*8192)*50; ry = (y - gy*8192)*50
        minx = min(minx, rx); maxx = max(maxx, rx)
        miny = min(miny, ry); maxy = max(maxy, ry)
print(f'Relative coords: x={minx:.0f}..{maxx:.0f}, y={miny:.0f}..{maxy:.0f}')
