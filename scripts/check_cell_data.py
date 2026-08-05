import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

# Parse the CELL at offset 91981 (after XCLC check from earlier output)
# Actually, let's find it properly
pos = 91899 + 24  # GRUP type=5 header + skip to content
# CELL record starts here
cell_sig = data[pos:pos+4]
cell_size = struct.unpack_from('<I', data, pos+4)[0]
cell_flags = struct.unpack_from('<I', data, pos+8)[0]
cell_fid = struct.unpack_from('<I', data, pos+12)[0]

print(f'CELL FID=0x{cell_fid:08X} size={cell_size} record_flags=0x{cell_flags:08X}')

# Parse all subrecords
sp = pos + 24
while sp < pos + 24 + cell_size - 6:
    ss = data[sp:sp+4]
    ssz = struct.unpack_from('<H', data, sp+4)[0]
    ss_name = ss.decode('ascii', errors='replace')
    
    print(f'  {ss_name} (size={ssz}): ', end='')
    
    if ss_name == 'EDID':
        edid = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode('ascii', errors='replace')
        print(edid)
    elif ss_name == 'DATA':
        val = struct.unpack_from('<I', data, sp+6)[0]
        print(f'0x{val:08X}')
        # Decode flags
        print(f'    Bit 0 (is exterior): {bool(val & 0x001)}')
        print(f'    Bit 1 (is water):    {bool(val & 0x002)}')
        print(f'    Bit 9 (use water):   {bool(val & 0x200)}')
    elif ss_name == 'XCLC':
        gx = struct.unpack_from('<i', data, sp+6)[0]
        gy = struct.unpack_from('<i', data, sp+10)[0]
        fl = struct.unpack_from('<I', data, sp+14)[0] if ssz >= 12 else 0
        print(f'grid=({gx},{gy}) flags=0x{fl:08X}')
    elif ss_name == 'XCLW':
        wh = struct.unpack_from('<f', data, sp+6)[0]
        print(f'{wh}')
    elif ss_name == 'LTMP':
        val = struct.unpack_from('<I', data, sp+6)[0]
        print(f'0x{val:08X}')
    elif ss_name == 'XILS':
        val = struct.unpack_from('<f', data, sp+6)[0]
        print(f'{val}')
    else:
        print(data[sp+6:sp+6+min(ssz, 20)].hex())
    
    sp += 6 + ssz

# Now check first REFR record
print('\n--- First REFR record ---')
refr_pos = 92029 + 24  # GRUP type=9 header + skip
# Skip GRUP header, find first REFR
rp = 92029 + 24  # inside GRUP type=9
sig = data[rp:rp+4]
sz = struct.unpack_from('<I', data, rp+4)[0]
fid = struct.unpack_from('<I', data, rp+12)[0]
print(f'REFR FID=0x{fid:08X} size={sz}')

rsp = rp + 24
while rsp < rp + 24 + sz - 6:
    ss = data[rsp:rsp+4]
    ssz = struct.unpack_from('<H', data, rsp+4)[0]
    ss_name = ss.decode('ascii', errors='replace')
    
    print(f'  {ss_name} (size={ssz}): ', end='')
    
    if ss_name == 'NAME':
        ref_fid = struct.unpack_from('<I', data, rsp+6)[0]
        print(f'0x{ref_fid:08X}')
    elif ss_name == 'DATA':
        x, y, z, rx, ry, rz = struct.unpack_from('<6f', data, rsp+6)
        print(f'pos=({x:.1f},{y:.1f},{z:.1f}) rot=({rx:.4f},{ry:.4f},{rz:.4f})')
    elif ss_name == 'EDID':
        edid = data[rsp+6:rsp+6+ssz].rstrip(b'\x00').decode('ascii', errors='replace')
        print(edid)
    else:
        print(data[rsp+6:rsp+6+min(ssz, 20)].hex())
    
    rsp += 6 + ssz

# Check how many subrecords each REFR has
print('\n--- REFR subrecord counts (first 5) ---')
rp = 92029 + 24  # inside GRUP type=9
for i in range(5):
    sig = data[rp:rp+4]
    if sig != b'REFR':
        break
    sz = struct.unpack_from('<I', data, rp+4)[0]
    fid = struct.unpack_from('<I', data, rp+12)[0]
    
    sub_count = 0
    sub_names = []
    rsp = rp + 24
    while rsp < rp + 24 + sz - 6:
        ss = data[rsp:rsp+4]
        ssz = struct.unpack_from('<H', data, rsp+4)[0]
        sub_names.append(ss.decode('ascii', errors='replace'))
        sub_count += 1
        rsp += 6 + ssz
    
    print(f'REFR 0x{fid:08X}: {sub_count} subrecords = {sub_names}')
    rp += 24 + sz
