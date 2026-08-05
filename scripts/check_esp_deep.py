import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')

# Parse STAT group
pos = 183 + 24
end = 183 + 45617
count = 0
fids = []
while pos < end - 24:
    sig = data[pos:pos+4]
    if sig != b'STAT':
        print(f'Non-STAT at {pos}: {sig}')
        break
    sz = struct.unpack_from('<I', data, pos+4)[0]
    fid = struct.unpack_from('<I', data, pos+12)[0]
    fids.append(fid)
    count += 1
    pos += 24 + sz

print(f'STAT records: {count}')
print(f'First FID: 0x{fids[0]:08X}')
print(f'Last FID:  0x{fids[-1]:08X}')

# Parse CELL group deeply
print('\n=== CELL GROUP ===')
pos = 45800 + 24
end = 45800 + 45530
depth = 0
cell_count = 0
refr_count = 0
grp_count = 0
first_few = True

while pos < end - 4:
    sig = data[pos:pos+4]
    if sig == b'GRUP':
        gs = struct.unpack_from('<I', data, pos+4)[0]
        gl = data[pos+8:pos+12].decode('ascii', errors='replace')
        gt = struct.unpack_from('<I', data, pos+12)[0]
        grp_count += 1
        if grp_count <= 10 or grp_count % 20 == 0:
            print(f'  GRUP [{gl}] type={gt} @ {pos}, size={gs}')
        pos += gs
    elif sig == b'CELL':
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        flags = struct.unpack_from('<I', data, pos+8)[0]
        cell_count += 1
        
        # Parse subrecords of first few cells
        if cell_count <= 3:
            is_compressed = bool(flags & 0x40000)
            print(f'  CELL FID=0x{fid:08X} size={sz} flags=0x{flags:08X} compressed={is_compressed}')
            
            if not is_compressed:
                sp = pos + 24
                while sp < pos + 24 + sz - 6:
                    ss = data[sp:sp+4].decode('ascii', errors='replace')
                    ssz = struct.unpack_from('<H', data, sp+4)[0]
                    
                    if ss == 'XCLC':
                        gx = struct.unpack_from('<i', data, sp+6)[0]
                        gy = struct.unpack_from('<i', data, sp+10)[0]
                        print(f'    XCLC: grid ({gx}, {gy})')
                    elif ss == 'DATA':
                        val = struct.unpack_from('<I', data, sp+6)[0]
                        print(f'    DATA: 0x{val:08X}')
                    elif ss == 'EDID':
                        edid = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode('ascii', errors='replace')
                        print(f'    EDID: {edid}')
                    elif ss == 'XCLW':
                        wh = struct.unpack_from('<f', data, sp+6)[0]
                        print(f'    XCLW: {wh}')
                    
                    sp += 6 + ssz
        
        pos += 24 + sz
    elif sig == b'REFR':
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        refr_count += 1
        
        if refr_count <= 3:
            print(f'  REFR FID=0x{fid:08X} size={sz}')
            sp = pos + 24
            while sp < pos + 24 + sz - 6:
                ss = data[sp:sp+4].decode('ascii', errors='replace')
                ssz = struct.unpack_from('<H', data, sp+4)[0]
                if ss == 'DATA':
                    x, y, z, rx, ry, rz = struct.unpack_from('<6f', data, sp+6)
                    print(f'    DATA: ({x:.1f}, {y:.1f}, {z:.1f}) rot=({rx:.4f}, {ry:.4f}, {rz:.4f})')
                elif ss == 'NAME':
                    ref_fid = struct.unpack_from('<I', data, sp+6)[0]
                    print(f'    NAME: 0x{ref_fid:08X}')
                elif ss == 'EDID':
                    edid = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode('ascii', errors='replace')
                    print(f'    EDID: {edid}')
                sp += 6 + ssz
        
        pos += 24 + sz
    else:
        print(f'  Unknown record at {pos}: {sig.hex()}')
        break

print(f'\nCELL group summary: {cell_count} cells, {refr_count} refrs, {grp_count} nested grups')
print(f'Parsed up to offset {pos}, group ends at {end}')
print(f'Remaining bytes: {end - pos}')

# Parse WRLD group deeply
print('\n=== WRLD GROUP ===')
pos = 91330 + 24
end = 91330 + 28499
while pos < end - 4:
    sig = data[pos:pos+4]
    if sig == b'GRUP':
        gs = struct.unpack_from('<I', data, pos+4)[0]
        gl = data[pos+8:pos+12].decode('ascii', errors='replace')
        gt = struct.unpack_from('<I', data, pos+12)[0]
        print(f'GRUP [{gl}] type={gt} @ {pos}, size={gs}')
        pos += gs
    elif sig == b'WRLD':
        sz = struct.unpack_from('<I', data, pos+4)[0]
        fid = struct.unpack_from('<I', data, pos+12)[0]
        flags = struct.unpack_from('<I', data, pos+8)[0]
        print(f'WRLD FID=0x{fid:08X} size={sz} flags=0x{flags:08X}')
        
        sp = pos + 24
        while sp < pos + 24 + sz - 6:
            ss = data[sp:sp+4].decode('ascii', errors='replace')
            ssz = struct.unpack_from('<H', data, sp+4)[0]
            if ss == 'EDID':
                edid = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode('ascii', errors='replace')
                print(f'  EDID: {edid}')
            elif ss == 'DNAM':
                a, b = struct.unpack_from('<2f', data, sp+6)
                print(f'  DNAM: ({a}, {b})')
            sp += 6 + ssz
        
        pos += 24 + sz
    else:
        print(f'Unexpected: {sig.decode("ascii", errors="replace")} @ {pos}')
        break
