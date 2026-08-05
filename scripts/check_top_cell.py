import struct

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

def read_grup(pos, depth=0):
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    try: label_str = label.decode('ascii')
    except: label_str = f'0x{label.hex()}'
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    end = pos + size
    inner = pos + 24
    records = []
    groups = []
    while inner < end:
        if data[inner:inner+4] == b'GRUP':
            inner, grp = read_grup(inner, depth+1)
            groups.append(grp)
        elif is_record_sig(data[inner:inner+4]):
            inner, rec = read_record(inner, depth+1)
            records.append(rec)
        else:
            inner += 1
    return end, (label_str, gtype, records, groups)

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    flags = struct.unpack('<I', data[pos+8:pos+12])[0]
    formid = struct.unpack('<I', data[pos+12:pos+16])[0]
    return pos + 16 + size, (sig, formid)

tes4_size = struct.unpack('<I', data[4:8])[0]
pos = 24 + tes4_size
while pos < len(data):
    if data[pos:pos+4] == b'GRUP':
        label = data[pos+8:pos+12]
        if label == b'CELL':
            _, grp = read_grup(pos, 0)
            print('Top CELL group:', grp)
            break
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 1
