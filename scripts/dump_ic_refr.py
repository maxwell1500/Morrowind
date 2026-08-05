import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0x65b2
size = struct.unpack('<I', data[pos+4:pos+8])[0]
flags = struct.unpack('<I', data[pos+8:pos+12])[0]
fid = struct.unpack('<I', data[pos+12:pos+16])[0]
print(f'REFR at 0x{pos:x}: size={size} flags=0x{flags:08X} fid=0x{fid:08X}')
body = data[pos+24:pos+24+size]
print(f'body hex: {body.hex()}')
sub = 0
while sub < len(body):
    ssig = body[sub:sub+4].decode('ascii', errors='replace')
    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
    payload = body[sub+6:sub+6+sln]
    print(f'  {ssig!r} len={sln} payload={payload.hex()}')
    sub += 6 + sln
