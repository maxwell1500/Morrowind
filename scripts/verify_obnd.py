"""Verify OBND values in the generated ESP."""
import struct

PATH = r"C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp"

with open(PATH, 'rb') as f:
    data = f.read()

print(f"ESP size: {len(data)} bytes")

# Find STAT records
idx = 0
count = 0
while idx < len(data):
    if data[idx:idx+4] == b'STAT':
        sig = data[idx:idx+4].decode('ascii')
        size = struct.unpack('<I', data[idx+4:idx+8])[0]
        flags = struct.unpack('<I', data[idx+8:idx+12])[0]
        formid = struct.unpack('<I', data[idx+12:idx+16])[0]
        # Read subrecords
        pos = idx + 24
        edid = None
        obnd = None
        while pos < idx + 24 + size:
            sub_sig = data[pos:pos+4].decode('ascii')
            sub_size = struct.unpack('<H', data[pos+4:pos+6])[0]
            sub_data = data[pos+6:pos+6+sub_size]
            if sub_sig == 'EDID':
                edid = sub_data.rstrip(b'\x00').decode('ascii', errors='replace')
            elif sub_sig == 'OBND':
                obnd = struct.unpack('<ffffff', sub_data)
            pos += 6 + sub_size
        if edid and obnd:
            print(f"  STAT 0x{formid:08X} {edid:35s} OBND: min=({obnd[0]:7.2f},{obnd[1]:7.2f},{obnd[2]:7.2f}) max=({obnd[3]:7.2f},{obnd[4]:7.2f},{obnd[5]:7.2f})")
        count += 1
        if count >= 10:
            break
        idx += 24 + size
    else:
        idx += 1

print(f"\nTotal STAT records checked: {count}")
