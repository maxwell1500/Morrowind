import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb') as f:
    data = f.read()

print(f'ESP size: {len(data)} bytes')

# Check TES4 header
sig = data[0:4]
print(f'TES4 sig: {sig}')
tes4_size = struct.unpack_from('<I', data, 4)[0]
tes4_flags = struct.unpack_from('<I', data, 8)[0]
print(f'TES4 flags: 0x{tes4_flags:08X}')
print(f'  ESM: {bool(tes4_flags & 1)}')
print(f'  ESL: {bool(tes4_flags & 0x200)}')

# Find all record types and count them
pos = 24  # skip TES4 header
record_counts = {}
while pos < len(data) - 24:
    rec_sig = data[pos:pos+4].decode('ascii', errors='replace')
    if not rec_sig.isalpha():
        break
    rec_size = struct.unpack_from('<I', data, pos+4)[0]
    rec_flags = struct.unpack_from('<I', data, pos+8)[0]
    rec_fid = struct.unpack_from('<I', data, pos+12)[0]
    
    if rec_sig not in record_counts:
        record_counts[rec_sig] = {'count': 0, 'fids': [], 'flags_set': set(), 'compressed': False}
    record_counts[rec_sig]['count'] += 1
    record_counts[rec_sig]['fids'].append(rec_fid)
    record_counts[rec_sig]['flags_set'].add(rec_flags)
    
    if rec_flags & 0x40000:
        record_counts[rec_sig]['compressed'] = True
    
    pos += 24 + rec_size

print(f'\nRecord counts:')
for sig, info in sorted(record_counts.items()):
    first = hex(info['fids'][0]) if info['fids'] else 'none'
    last = hex(info['fids'][-1]) if info['fids'] else 'none'
    flags_list = [hex(f) for f in info['flags_set']]
    compressed = ' [COMPRESSED]' if info['compressed'] else ''
    print(f'  {sig}: {info["count"]} records, FID range {first}-{last}, flags={flags_list}{compressed}')

# Check if FExxxx formIDs are being used correctly
# For ESL (light) plugins, formIDs should be 0xFExxx where xxx is the local formID
for sig, info in record_counts.items():
    for fid in info['fids']:
        if (fid >> 24) == 0xFE:
            local_id = fid & 0xFFF
            # Check for collisions - two records with same local ID
            pass

# Check for formID collisions in the FE range
fe_records = {}
for sig, info in record_counts.items():
    for fid in info['fids']:
        if (fid >> 24) == 0xFE:
            local_id = fid & 0xFFF
            key = hex(fid)
            if key not in fe_records:
                fe_records[key] = []
            fe_records[key].append(sig)

collisions = {k: v for k, v in fe_records.items() if len(v) > 1}
if collisions:
    print(f'\nFORMID COLLISIONS:')
    for fid, sigs in sorted(collisions.items()):
        print(f'  {fid}: {", ".join(sigs)}')
else:
    print(f'\nNo formID collisions in FE range')

# Check WRLD record specifically
print(f'\n--- WRLD record details ---')
pos = 24
while pos < len(data) - 24:
    rec_sig = data[pos:pos+4].decode('ascii', errors='replace')
    rec_size = struct.unpack_from('<I', data, pos+4)[0]
    rec_flags = struct.unpack_from('<I', data, pos+8)[0]
    rec_fid = struct.unpack_from('<I', data, pos+12)[0]
    
    if rec_sig == 'WRLD':
        print(f'  WRLD at offset {pos}: size={rec_size}, flags=0x{rec_flags:08X}, FID=0x{rec_fid:08X}')
        # Check if flags indicate override
        if rec_flags & 0x04:
            print(f'  -> This is an OVERRIDE record')
        else:
            print(f'  -> This is a NEW record (NOT override!)')
    
    pos += 24 + rec_size
