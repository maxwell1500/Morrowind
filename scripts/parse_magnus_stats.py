"""Parse Magnus.esm to look at STAT records and their subrecords."""
import struct

PATH = r"C:\XboxGames\Starfield\Content\Data\The Elder Star System - Magnus.esm"

with open(PATH, 'rb') as f:
    data = f.read()

print(f"Magnus.esm size: {len(data)} bytes")

# Find STAT records
count = 0
obnd_seen = []
all_subrecords = {}
i = 0
while i < len(data) - 24:
    sig = data[i:i+4]
    if sig == b'STAT':
        size = struct.unpack('<I', data[i+4:i+8])[0]
        flags = struct.unpack('<I', data[i+8:i+12])[0]
        formid = struct.unpack('<I', data[i+12:i+16])[0]
        # Read subrecords
        pos = i + 24
        end = pos + size
        subs = []
        while pos < end - 6:
            sub_sig = data[pos:pos+4]
            if not sub_sig.isalpha():
                break
            try:
                sub_size = struct.unpack('<H', data[pos+4:pos+6])[0]
                sub_data = data[pos+6:pos+6+sub_size]
                subs.append((sub_sig.decode('ascii', errors='replace'), sub_size))
                all_subrecords[sub_sig.decode('ascii', errors='replace')] = all_subrecords.get(sub_sig.decode('ascii', errors='replace'), 0) + 1
                if sub_sig == b'OBND':
                    obnd = struct.unpack('<ffffff', sub_data)
                    obnd_seen.append(obnd)
                pos += 6 + sub_size
            except:
                break
        if count < 5:
            print(f"  STAT 0x{formid:08X} flags=0x{flags:08X}: {subs}")
        count += 1
        i = end
    else:
        i += 1

print(f"\nTotal STAT records: {count}")
print(f"\nSubrecord frequency:")
for k, v in sorted(all_subrecords.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

if obnd_seen:
    print(f"\nSample OBND values ({len(obnd_seen)} total):")
    for obnd in obnd_seen[:5]:
        print(f"  {obnd}")
