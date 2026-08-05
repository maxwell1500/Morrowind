import struct

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    flags = struct.unpack('<I', data[pos+8:pos+12])[0]
    formid = struct.unpack('<I', data[pos+12:pos+16])[0]
    indent = '  ' * depth
    print(f'{indent}RECORD {sig} at 0x{pos:x} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
    if formid == 0x00000240:
        print(f'{indent}^^^ FOUND 0x240 formID!')
    return pos + 16 + size

def read_grup(pos, depth=0):
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    try: label_str = label.decode('ascii')
    except: label_str = f'0x{label.hex()}'
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    end = pos + size
    indent = '  ' * depth
    print(f'{indent}GRUP {label_str!r} type={gtype} at 0x{pos:x} size={size}')
    inner = pos + 24
    while inner < end:
        if data[inner:inner+4] == b'GRUP':
            inner = read_grup(inner, depth+1)
        elif is_record_sig(data[inner:inner+4]):
            inner = read_record(inner, depth+1)
        else:
            print(f'{"  "*(depth+1)}Unknown at 0x{inner:x}: {data[inner:inner+4].hex()}')
            inner += 1
    return end

tes4_size = struct.unpack('<I', data[4:8])[0]
pos = 24 + tes4_size
while pos < len(data):
    pos = read_grup(pos, 0)
