import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos = 0xa9
size = struct.unpack('<I', data[pos+4:pos+8])[0]
content = data[pos+16:pos+16+size]
print('size field', size, 'expected 144')
# skip prefix
sub = 8
end = len(content)
while sub < end:
    ssig = content[sub:sub+4].decode('ascii', errors='replace')
    sln = struct.unpack('<H', content[sub+4:sub+6])[0]
    print(f'  {ssig!r} len={sln}')
    sub += 6 + sln
print('parsed end', sub, 'content len', len(content))
