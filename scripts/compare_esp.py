import struct, os

paths = [
    r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm',
    r'C:\XboxGames\Starfield\Content\Data\SeydaNeen.esp'
]

for path in paths:
    print(f'\n{"="*60}')
    print(f'FILE: {path}')
    print('='*60)
    data = open(path, 'rb').read()

    def is_record_sig(b):
        return len(b) == 4 and all(32 <= c <= 126 for c in b)

    def read_record(pos, depth=0):
        sig = data[pos:pos+4].decode('ascii', errors='replace')
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', data[pos+8:pos+12])[0]
        formid = struct.unpack('<I', data[pos+12:pos+16])[0]
        print(f'{"  "*depth}RECORD at 0x{pos:x}: {sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
        return pos + 16 + size

    def read_grup(pos, depth=0):
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        label = data[pos+8:pos+12]
        try: label_str = label.decode('ascii')
        except: label_str = f'0x{label.hex()}'
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        end = pos + size
        print(f'{"  "*depth}GRUP at 0x{pos:x}: label={label_str!r} type={gtype} size={size}')
        inner = pos + 24
        while inner < end:
            if data[inner:inner+4] == b'GRUP':
                inner = read_grup(inner, depth+1)
            elif is_record_sig(data[inner:inner+4]):
                inner = read_record(inner, depth+1)
            else:
                inner += 1
        return end

    print('=== TES4 Header ===')
    print(f'sig={data[0:4].decode()} size={struct.unpack("<I", data[4:8])[0]} flags=0x{struct.unpack("<I", data[8:12])[0]:08X}')
    print(f'bytes 0x10-0x13: {data[0x10:0x14].hex()}')
    print(f'bytes 0x14-0x17: {data[0x14:0x18].hex()}')

    tes4_size = struct.unpack('<I', data[4:8])[0]
    pos = 24 + tes4_size
    print(f'\n=== Top-level groups starting at 0x{pos:x} (file size {len(data)}) ===')
    count = 0
    while pos < len(data) and count < 30:
        pos = read_grup(pos, 0)
        print()
        count += 1
