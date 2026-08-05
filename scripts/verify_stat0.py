import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
pos = 0xa9
size = struct.unpack('<I', data[pos+4:pos+8])[0]
body = data[pos+24:pos+24+size]
print('STAT0 size', size, 'body len', len(body))
sub = 0
while sub < len(body):
    ssig = body[sub:sub+4].decode('ascii', errors='replace')
    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
    print(f'  {ssig!r} len={sln}')
    sub += 6 + sln
print('next record at', hex(pos+24+size), 'is', data[pos+24+size:pos+24+size+4].decode())
