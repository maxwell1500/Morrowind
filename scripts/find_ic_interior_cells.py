import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

def parse_grup(pos, depth=0, path=None):
    if path is None: path = []
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    try: label_str = label.decode('ascii')
    except: label_str = f'0x{label.hex()}'
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    end = pos + size
    inner = pos + 24
    cell_info = []
    while inner < end:
        if data[inner:inner+4] == b'GRUP':
            cell_info.extend(parse_grup(inner, depth+1, path + [(gtype, label_str)]))
            inner += struct.unpack('<I', data[inner+4:inner+8])[0]
        elif is_record_sig(data[inner:inner+4]):
            sig = data[inner:inner+4].decode('ascii', errors='replace')
            rsize = struct.unpack('<I', data[inner+4:inner+8])[0]
            flags = struct.unpack('<I', data[inner+8:inner+12])[0]
            formid = struct.unpack('<I', data[inner+12:inner+16])[0]
            if sig == 'CELL':
                rec = data[inner+16:inner+16+rsize]
                try:
                    if flags & 0x00040000:
                        rec = __import__('zlib').decompress(rec[12:])
                    elif rec[:8] == b'\x00\x00\x00\x00@\x02\x00\x00':
                        rec = rec[8:]
                    has_xclc = False
                    edid = ''
                    i = 0
                    while i < len(rec) - 6:
                        sub_sig = rec[i:i+4].decode('ascii', errors='replace')
                        sub_len = struct.unpack('<H', rec[i+4:i+6])[0]
                        if sub_sig == 'XCLC':
                            has_xclc = True
                        if sub_sig == 'EDID':
                            edid = rec[i+6:i+6+sub_len].split(b'\x00')[0].decode('ascii', errors='replace')
                        i += 6 + sub_len
                    if not has_xclc:
                        cell_info.append((formid, edid, path + [(gtype, label_str)]))
                except:
                    pass
            inner += 16 + rsize
        else:
            inner += 1
    return cell_info

tes4_size = struct.unpack('<I', data[4:8])[0]
pos = 24 + tes4_size
all_cells = []
while pos < len(data):
    if data[pos:pos+4] == b'GRUP':
        label = data[pos+8:pos+12]
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        if label == b'CELL':
            all_cells.extend(parse_grup(pos, 0, []))
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 1

print(f'Found {len(all_cells)} interior cells in ImperialCity')
for fid, edid, path in all_cells[:20]:
    print(f'CELL 0x{fid:08X} {edid} path={path}')
