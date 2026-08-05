import struct, sys

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

def dump_group(data, pos, end, depth=0):
    indent = '  ' * depth
    while pos < end - 4:
        sig = data[pos:pos+4]
        if sig == b'GRUP':
            gs = struct.unpack_from('<I', data, pos+4)[0]
            if gs < 24 or pos + gs > end:
                print(f'{indent}Bad GRUP size {gs} at {pos}')
                break
            label_raw = data[pos+8:pos+12]
            gt = struct.unpack_from('<I', data, pos+12)[0]
            
            # Format label
            if gt == 1:
                label = f'wrld=0x{struct.unpack_from("<I", label_raw)[0]:08X}'
            elif gt in (4, 5):
                bx, by = struct.unpack_from('<2h', label_raw)
                label = f'block({bx},{by})'
            elif gt in (6, 8, 9):
                label = f'cell=0x{struct.unpack_from("<I", label_raw)[0]:08X}'
            elif gt in (2, 3):
                label = str(struct.unpack_from('<i', label_raw)[0])
            else:
                label = label_raw.hex()
            
            print(f'{indent}GRUP type={gt} [{label}] @ {pos} size={gs}')
            dump_group(data, pos + 24, pos + gs, depth + 1)
            pos += gs
        elif sig == b'CELL':
            sz = struct.unpack_from('<I', data, pos+4)[0]
            fid = struct.unpack_from('<I', data, pos+12)[0]
            flags = struct.unpack_from('<I', data, pos+8)[0]
            compressed = bool(flags & 0x40000)
            
            xclc_info = ''
            if not compressed:
                sp = pos + 24
                while sp < pos + 24 + sz - 6:
                    ss = data[sp:sp+4]
                    ssz = struct.unpack_from('<H', data, sp+4)[0]
                    if ss == b'XCLC':
                        gx = struct.unpack_from('<i', data, sp+6)[0]
                        gy = struct.unpack_from('<i', data, sp+10)[0]
                        xclc_info = f' XCLC=({gx},{gy})'
                        break
                    sp += 6 + ssz
            
            print(f'{indent}CELL FID=0x{fid:08X} flags=0x{flags:08X} comp={compressed}{xclc_info}')
            pos += 24 + sz
        elif sig == b'REFR':
            sz = struct.unpack_from('<I', data, pos+4)[0]
            fid = struct.unpack_from('<I', data, pos+12)[0]
            print(f'{indent}REFR FID=0x{fid:08X} size={sz}')
            pos += 24 + sz
        elif sig == b'WRLD':
            sz = struct.unpack_from('<I', data, pos+4)[0]
            fid = struct.unpack_from('<I', data, pos+12)[0]
            print(f'{indent}WRLD FID=0x{fid:08X} size={sz}')
            pos += 24 + sz
        else:
            try:
                name = sig.decode('ascii')
            except:
                name = sig.hex()
            print(f'{indent}??? [{name}] @ {pos}')
            break

# Start from the WRLD group children (GRUP type=1)
pos = 91720 + 24  # skip GRUP type=1 header
end = 91720 + 28109
dump_group(data, pos, end, 0)
