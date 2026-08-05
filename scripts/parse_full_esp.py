import struct, zlib

data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()

def is_record_sig(b):
    return len(b) == 4 and all(32 <= c <= 126 for c in b)

def read_record(pos, depth=0):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    flags = struct.unpack('<I', data[pos+8:pos+12])[0]
    formid = struct.unpack('<I', data[pos+12:pos+16])[0]
    return pos + 16 + size, (sig, formid)

def read_grup(pos, depth=0):
    size = struct.unpack('<I', data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    try: label_str = label.decode('ascii')
    except: label_str = f'0x{label.hex()}'
    gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
    end = pos + size
    inner = pos + 24
    records = []
    groups = []
    while inner < end:
        if data[inner:inner+4] == b'GRUP':
            inner, grp = read_grup(inner, depth+1)
            groups.append(grp)
        elif is_record_sig(data[inner:inner+4]):
            inner, rec = read_record(inner, depth+1)
            records.append(rec)
        else:
            inner += 1
    return end, (label_str, gtype, records, groups)

tes4_size = struct.unpack('<I', data[4:8])[0]
pos = 24 + tes4_size
summary = []
while pos < len(data):
    pos, grp = read_grup(pos, 0)
    summary.append(grp)

# Print summary
def summarize(grp, depth=0):
    label, gtype, records, groups = grp
    indent = '  ' * depth
    print(f'{indent}GRUP {label} type={gtype}: {len(records)} records, {len(groups)} child groups')
    for sig, fid in records[:5]:
        print(f'{indent}  {sig} 0x{fid:08X}')
    if len(records) > 5:
        print(f'{indent}  ... ({len(records)-5} more)')
    for g in groups:
        summarize(g, depth+1)

for g in summary:
    summarize(g)

# Counts
all_records = []
def collect(grp):
    label, gtype, records, groups = grp
    all_records.extend(records)
    for g in groups:
        collect(g)
for g in summary:
    collect(g)
print('\n=== Totals ===')
from collections import Counter
c = Counter(sig for sig, _ in all_records)
for sig, cnt in c.most_common():
    print(f'{sig}: {cnt}')
print(f'Total records: {len(all_records)}')
