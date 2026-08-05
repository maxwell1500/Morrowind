import struct, zlib

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

hits = []

def parse_subrecords(rec_body, sig, formid):
    i = 0
    while i < len(rec_body) - 6:
        sub_sig = rec_body[i:i+4].decode('ascii', errors='replace')
        try:
            sub_len = struct.unpack('<H', rec_body[i+4:i+6])[0]
        except:
            i += 1
            continue
        sub_data = rec_body[i+6:i+6+sub_len]
        # scan every 4-byte aligned value in this subrecord data
        for j in range(0, max(0, len(sub_data) - 3), 4):
            val = struct.unpack('<I', sub_data[j:j+4])[0]
            if val == 0x00000240:
                hits.append((sig, hex(formid), sub_sig, j, sub_data.hex()[:64]))
        i += 6 + sub_len

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    flags = struct.unpack('<I', data[pos+8:pos+12])[0]
    formid = struct.unpack('<I', data[pos+12:pos+16])[0]
    rec = data[pos+16:pos+16+size]
    if flags & 0x00040000:
        try:
            rec = zlib.decompress(rec[12:])
            body = rec
        except Exception as e:
            print(f'decompress error at {sig} {hex(formid)}: {e}')
            return pos + 16 + size
    else:
        if rec[:8] == b'\x00\x00\x00\x00@\x02\x00\x00':
            body = rec[8:]
        else:
            body = rec
    parse_subrecords(body, sig, formid)
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

if hits:
    print('Found 0x00000240 as 4-byte value in subrecords:')
    for h in hits:
        print(f'  {h}')
else:
    print('No 0x00000240 found as 4-byte value in any subrecord data.')
