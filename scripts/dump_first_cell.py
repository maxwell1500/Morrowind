import struct, zlib

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    flags = struct.unpack('<I', data[pos+8:pos+12])[0]
    formid = struct.unpack('<I', data[pos+12:pos+16])[0]
    rec = data[pos+16:pos+16+size]
    if flags & 0x00040000:
        rec = zlib.decompress(rec[12:])
    elif rec[:8] == b'\x00\x00\x00\x00@\x02\x00\x00':
        rec = rec[8:]
    else:
        rec = rec
    print(f'{"  "*depth}RECORD {sig} 0x{formid:08X}')
    i = 0
    while i < len(rec) - 6:
        sub_sig = rec[i:i+4].decode('ascii', errors='replace')
        sub_len = struct.unpack('<H', rec[i+4:i+6])[0]
        sub_data = rec[i+6:i+6+sub_len]
        print(f'{"  "*depth}  {sub_sig} len={sub_len} data={sub_data.hex()[:40]}')
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
# read first few top-level groups, find first CELL
while pos < len(data):
    if data[pos:pos+4] == b'GRUP':
        label = data[pos+8:pos+12]
        if label == b'CELL':
            read_grup(pos, 0)
            break
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 1
