import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

print(f'ESP size: {len(data)} bytes')

# TES4 header
print(f'TES4 flags: 0x{struct.unpack_from("<I", data, 8)[0]:08X}')
print(f'  ESM: {bool(struct.unpack_from("<I", data, 8)[0] & 1)}')
print(f'  ESL (light): {bool(struct.unpack_from("<I", data, 8)[0] & 0x200)}')

# Parse top-level structure
pos = 0
while pos < len(data) - 24:
    sig = data[pos:pos+4]
    if sig == b'TES4':
        size = struct.unpack_from('<I', data, pos+4)[0]
        pos += 24 + size  # TES4 header is 24 bytes + data
        continue
    elif sig == b'GRUP':
        grp_size = struct.unpack_from('<I', data, pos+4)[0]
        grp_label = data[pos+8:pos+12]
        grp_type = struct.unpack_from('<I', data, pos+12)[0]
        label_str = grp_label.decode('ascii', errors='replace')
        print(f'\nGRUP "{label_str}" (type={grp_type}) at offset {pos}, size={grp_size}')
        
        # Parse records inside GRUP
        grp_end = pos + grp_size
        inner_pos = pos + 24  # skip GRUP header
        
        while inner_pos < grp_end - 24:
            rec_sig = data[inner_pos:inner_pos+4]
            
            if rec_sig == b'GRUP':
                # Nested GRUP - skip
                nested_size = struct.unpack_from('<I', data, inner_pos+4)[0]
                inner_pos += nested_size
                continue
            
            rec_size = struct.unpack_from('<I', data, inner_pos+4)[0]
            rec_flags = struct.unpack_from('<I', data, inner_pos+8)[0]
            rec_fid = struct.unpack_from('<I', data, inner_pos+12)[0]
            
            sig_str = rec_sig.decode('ascii', errors='replace')
            fid_hex = f'0x{rec_fid:08X}'
            override = ' [OVERRIDE]' if rec_flags & 0x04 else ''
            compressed = ' [COMPRESSED]' if rec_flags & 0x40000 else ''
            print(f'  {sig_str} FID={fid_hex} size={rec_size} flags=0x{rec_flags:08X}{override}{compressed}')
            
            # For STAT/REFR records, show first few
            if sig_str in ('STAT', 'REFR', 'WRLD', 'CELL'):
                if rec_size > 0:
                    # Show first subrecord
                    sub_start = inner_pos + 24
                    sub_sig = data[sub_start:sub_start+4].decode('ascii', errors='replace')
                    print(f'    First sub: {sub_sig}')
            
            inner_pos += 24 + rec_size
        
        pos = grp_end
    else:
        # Unknown, skip
        print(f'Unknown block: {sig} at offset {pos}')
        break
