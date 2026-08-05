import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos = 0xa9
size = struct.unpack('<I', data[pos+4:pos+8])[0]
content = data[pos+16:pos+16+size]
# skip 8-byte prefix
sub_data = content[8:]
print('sub_data length', len(sub_data))
# parse as subrecords
sub = 0
end = len(sub_data)
while sub < end:
    ssig = sub_data[sub:sub+4].decode('ascii', errors='replace')
    sln = struct.unpack('<H', sub_data[sub+4:sub+6])[0]
    payload = sub_data[sub+6:sub+6+sln]
    print(f'  0x{sub:x}: {ssig!r} len={sln} payload={payload[:80]}')
    sub += 6 + sln
    if sub > end:
        print('  OVERRUN')
        break
print(f'Parsed sub_data end at 0x{sub:x}, total 0x{end:x}')
