import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

# TES4 flags detailed
tes4_flags = struct.unpack_from('<I', data, 8)[0]
print(f'TES4 flags: 0x{tes4_flags:08X}')
print(f'  Bit 0  (ESM master):     {bool(tes4_flags & 0x001)}')
print(f'  Bit 8  (0x100):          {bool(tes4_flags & 0x100)}')
print(f'  Bit 9  (ESL/light):      {bool(tes4_flags & 0x200)}')
print(f'  Bit 10 (0x400):          {bool(tes4_flags & 0x400)}')

# Starfield uses 0x100 for ESL, not 0x200 like Skyrim/FO4
print(f'\n  Starfield ESL flag is 0x100, not 0x200')
print(f'  ESL is {"SET" if tes4_flags & 0x100 else "NOT SET"}')

# Now parse GRUPs properly, handling compressed records
pos = 24  # Skip TES4 header
while pos < len(data) - 4:
    sig = data[pos:pos+4]
    if sig == b'GRUP':
        grp_size = struct.unpack_from('<I', data, pos+4)[0]
        grp_label = data[pos+8:pos+12].decode('ascii', errors='replace')
        grp_type = struct.unpack_from('<I', data, pos+12)[0]
        
        # Only process CELL and WRLD groups
        if grp_label in ('CELL', 'WRLD', 'REFR'):
            print(f'\n=== GRUP "{grp_label}" (type={grp_type}) at {pos}, size={grp_size} ===')
            
            inner_pos = pos + 24
            grp_end = pos + grp_size
            count = 0
            
            while inner_pos < grp_end - 24:
                inner_sig = data[inner_pos:inner_pos+4]
                
                if inner_sig == b'GRUP':
                    nested_size = struct.unpack_from('<I', data, inner_pos+4)[0]
                    if grp_label == 'CELL':
                        nested_label = data[inner_pos+8:inner_pos+12].decode('ascii', errors='replace')
                        print(f'  Nested GRUP type={nested_label} at {inner_pos}, size={nested_size}')
                    inner_pos += nested_size
                    continue
                
                rec_size = struct.unpack_from('<I', data, inner_pos+4)[0]
                rec_flags = struct.unpack_from('<I', data, inner_pos+8)[0]
                rec_fid = struct.unpack_from('<I', data, inner_pos+12)[0]
                
                is_compressed = bool(rec_flags & 0x40000)
                
                if count < 5:  # Show first 5 records
                    print(f'  {inner_sig.decode("ascii","?")} FID=0x{rec_fid:08X} size={rec_size} flags=0x{rec_flags:08X} compressed={is_compressed}')
                
                count += 1
                
                # For CELL records, show subrecords
                if inner_sig == b'CELL' and count <= 2:
                    sub_pos = inner_pos + 24
                    while sub_pos < inner_pos + 24 + rec_size - 4:
                        sub_sig = data[sub_pos:sub_pos+4].decode('ascii', errors='replace')
                        sub_size = struct.unpack_from('<H', data, sub_pos+4)[0] if sub_pos+6 <= len(data) else 0
                        
                        if sub_sig == 'XCLC':
                            gx = struct.unpack_from('<i', data, sub_pos+6)[0]
                            gy = struct.unpack_from('<i', data, sub_pos+10)[0]
                            print(f'    XCLC: grid ({gx}, {gy})')
                        elif sub_sig == 'DATA':
                            val = struct.unpack_from('<I', data, sub_pos+6)[0]
                            print(f'    DATA: 0x{val:08X}')
                        
                        sub_pos += 6 + sub_size
                
                inner_pos += 24 + rec_size
            
            if grp_label != 'CELL' or count > 0:
                print(f'  Total records: {count}')
        
        pos += grp_size
    else:
        break
