import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

# The WRLD group starts at 91330
wrld_grp_start = 91330
wrld_grp_size = 28499
wrld_grp_end = wrld_grp_start + wrld_grp_size

pos = wrld_grp_start + 24  # skip GRUP header

# Walk through WRLD children
while pos < wrld_grp_end - 4:
    sig = data[pos:pos+4]
    if sig == b'GRUP':
        gs = struct.unpack_from('<I', data, pos+4)[0]
        label_raw = data[pos+8:pos+12]
        gt = struct.unpack_from('<I', data, pos+12)[0]
        
        if gt == 1:
            label = f'WRLD children of 0x{struct.unpack_from("<I", label_raw)[0]:08X}'
        elif gt in (4, 5):
            bx, by = struct.unpack_from('<2h', label_raw)
            label = f'block({bx},{by})'
        elif gt in (6, 8, 9):
            label = f'0x{struct.unpack_from("<I", label_raw)[0]:08X}'
        elif gt == 2 or gt == 3:
            v = struct.unpack_from('<i', label_raw)[0]
            label = str(v)
        else:
            label = label_raw.hex()
        
        print(f'GRUP type={gt} [{label}] @ {pos}, size={gs}')
        
        if gt <= 1:  # recurse into type 0, 1
            pos += gs
            continue
        else:
            pos += gs
    elif sig == b'WRLD':
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        print(f'  WRLD FID=0x{fid:08X} size={sz}')
        pos += 24 + sz
    elif sig == b'CELL':
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        flags = struct.unpack_from('<I', data, pos+8)[0]
        compressed = bool(flags & 0x40000)
        
        # Read XCLC from subrecords
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
        
        print(f'  CELL FID=0x{fid:08X} flags=0x{flags:08X} comp={compressed}{xclc_info}')
        pos += 24 + sz
    elif sig == b'REFR':
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        pos += 24 + sz
    else:
        try:
            name = sig.decode('ascii')
        except:
            name = sig.hex()
        print(f'  Unknown [{name}] @ {pos}')
        break

print(f'\nFinal pos: {pos}, expected end: {wrld_grp_end}')
print(f'Match: {pos == wrld_grp_end}')
