import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Parse WRLD group deeply
pos = 91330 + 24
end = 91330 + 28499

def parse_group(data, pos, end, depth=0):
    indent = '  ' * depth
    while pos < end - 4:
        sig = data[pos:pos+4]
        if sig == b'GRUP':
            gs = struct.unpack_from('<I', data, pos+4)[0]
            gl = data[pos+8:pos+12]
            gt = struct.unpack_from('<I', data, pos+12)[0]
            # Label interpretation depends on group type
            if gt == 1:
                label = f'0x{struct.unpack_from("<I", gl)[0]:08X}'
            elif gt in (2, 3):
                label = str(struct.unpack_from('<i', gl)[0])
            elif gt in (4, 5):
                bx, by = struct.unpack_from('<2h', gl)
                label = f'({bx}, {by})'
            elif gt in (6, 8, 9):
                label = f'0x{struct.unpack_from("<I", gl)[0]:08X}'
            else:
                label = gl.hex()
            print(f'{indent}GRUP type={gt} label=[{label}] @ {pos}, size={gs}')
            parse_group(data, pos + 24, pos + gs, depth + 1)
            pos += gs
        elif sig in (b'CELL', b'REFR', b'WRLD', b'LCTN', b'STAT'):
            sz = struct.unpack_from('<I', data, pos+4)[0]
            fid = struct.unpack_from('<I', data, pos+12)[0]
            flags = struct.unpack_from('<I', data, pos+8)[0]
            is_compressed = bool(flags & 0x40000)
            
            if sig == b'REFR':
                print(f'{indent}REFR FID=0x{fid:08X} size={sz} flags=0x{flags:08X} compressed={is_compressed}')
                if not is_compressed:
                    sp = pos + 24
                    while sp < pos + 24 + min(sz, 500) - 6:
                        ss = data[sp:sp+4]
                        ssz = struct.unpack_from('<H', data, sp+4)[0]
                        try:
                            ss_str = ss.decode('ascii')
                        except:
                            ss_str = ss.hex()
                        if ss_str == 'DATA' and ssz == 24:
                            x, y, z, rx, ry, rz = struct.unpack_from('<6f', data, sp+6)
                            print(f'{indent}  DATA: ({x:.1f}, {y:.1f}, {z:.1f}) rot=({rx:.4f}, {ry:.4f}, {rz:.4f})')
                        elif ss_str == 'NAME':
                            ref_fid = struct.unpack_from('<I', data, sp+6)[0]
                            print(f'{indent}  NAME: 0x{ref_fid:08X}')
                        sp += 6 + ssz
                pos += 24 + sz
            elif sig == b'CELL':
                print(f'{indent}CELL FID=0x{fid:08X} size={sz} flags=0x{flags:08X} compressed={is_compressed}')
                if not is_compressed:
                    sp = pos + 24
                    while sp < pos + 24 + sz - 6:
                        ss = data[sp:sp+4]
                        ssz = struct.unpack_from('<H', data, sp+4)[0]
                        try:
                            ss_str = ss.decode('ascii')
                        except:
                            ss_str = ss.hex()
                        if ss_str == 'XCLC':
                            gx = struct.unpack_from('<i', data, sp+6)[0]
                            gy = struct.unpack_from('<i', data, sp+10)[0]
                            print(f'{indent}  XCLC: grid ({gx}, {gy})')
                        elif ss_str == 'EDID':
                            edid = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode('ascii', errors='replace')
                            print(f'{indent}  EDID: {edid}')
                        elif ss_str == 'DATA':
                            val = struct.unpack_from('<I', data, sp+6)[0]
                            print(f'{indent}  DATA: 0x{val:08X}')
                        elif ss_str == 'XCLW':
                            wh = struct.unpack_from('<f', data, sp+6)[0]
                            print(f'{indent}  XCLW: {wh}')
                        sp += 6 + ssz
                pos += 24 + sz
            elif sig == b'WRLD':
                print(f'{indent}WRLD FID=0x{fid:08X} size={sz} flags=0x{flags:08X}')
                pos += 24 + sz
            else:
                print(f'{indent}{sig.decode("ascii")} FID=0x{fid:08X} size={sz}')
                pos += 24 + sz
        else:
            try:
                name = sig.decode('ascii')
            except:
                name = sig.hex()
            print(f'{indent}??? Unknown record [{name}] @ {pos}')
            break

parse_group(data, pos, end, 0)
