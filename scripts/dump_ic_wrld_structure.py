import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

def dump_grup(pos, depth=0):
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    try: label_str = label.decode('ascii')
    except: label_str = f'0x{label.hex()}'
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    end = pos + size
    print(f'{"  "*depth}GRUP label={label_str!r} type={gtype} size={size} at 0x{pos:x}')
    inner = pos + 24
    while inner < end:
        if data[inner:inner+4] == b'GRUP':
            dump_grup(inner, depth+1)
            inner += struct.unpack('<I', data[inner+4:inner+8])[0]
        elif is_record_sig(data[inner:inner+4]):
            sig = data[inner:inner+4].decode('ascii', errors='replace')
            rsize = struct.unpack('<I', data[inner+4:inner+8])[0]
            flags = struct.unpack('<I', data[inner+8:inner+12])[0]
            formid = struct.unpack('<I', data[inner+12:inner+16])[0]
            print(f'{"  "*(depth+1)}RECORD {sig} 0x{formid:08X} size={rsize} flags=0x{flags:08X}')
            inner += 16 + rsize
        else:
            inner += 1

# Find WRLD top-level group
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    if data[pos:pos+4] == b'GRUP':
        label = data[pos+8:pos+12]
        if label == b'WRLD':
            dump_grup(pos, 0)
            break
        pos += struct.unpack('<I', data[pos+4:pos+8])[0]
    else:
        pos += 1
