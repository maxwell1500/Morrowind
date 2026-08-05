import struct, zlib

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

formid_240_locs = []

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    flags = struct.unpack('<I', data[pos+8:pos+12])[0]
    formid = struct.unpack('<I', data[pos+12:pos+16])[0]
    rec = data[pos+16:pos+16+size]
    if flags & 0x00040000:
        rec = zlib.decompress(rec[12:])
        body = rec
    else:
        # strip 8-byte prefix if present
        if rec[:8] == b'\x00\x00\x00\x00@\x02\x00\x00':
            body = rec[8:]
        else:
            body = rec
    i = 0
    while i < len(body) - 6:
        sub_sig = body[i:i+4].decode('ascii', errors='replace')
        try:
            sub_len = struct.unpack('<H', body[i+4:i+6])[0]
        except:
            i += 1
            continue
        sub_data = body[i+6:i+6+sub_len]
        if len(sub_data) == 4:
            val = struct.unpack('<I', sub_data)[0]
            if val == 0x00000240:
                formid_240_locs.append((sig, formid, sub_sig, i, val))
        i += 6 + sub_len
    return pos + 16 + size

def read_grup(pos, depth=0):
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    end = pos + size
    inner = pos + 24
    while inner < end:
        if data[inner:inner+4] == b'GRUP':
            inner = read_grup(inner, depth+1)
        elif is_record_sig(data[inner:inner+4]):
            inner = read_record(inner, depth+1)
        else:
            inner += 1
    return end

tes4_size = struct.unpack('<I', data[4:8])[0]
pos = 24 + tes4_size
while pos < len(data):
    pos = read_grup(pos, 0)

if formid_240_locs:
    print('Found 0x00000240 in subrecords:')
    for sig, formid, sub_sig, offset, val in formid_240_locs:
        print(f'  RECORD {sig} formid=0x{formid:08X}, subrecord {sub_sig} at body offset {offset}: 0x{val:08X}')
else:
    print('No 0x00000240 found in any subrecord data.')
