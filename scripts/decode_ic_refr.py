import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
# Find first REFR at 0x65b2
pos = 0x65b2
size = struct.unpack('<I', data[pos+4:pos+8])[0]
body = data[pos+24:pos+24+size]
# NAME first 4 bytes
sub = 0
ssig = body[sub:sub+4].decode()
sln = struct.unpack('<H', body[sub+4:sub+6])[0]
name = struct.unpack('<I', body[sub+6:sub+6+sln])[0]
print(f'REFR NAME 0x{name:08X}')
sub += 6 + sln
ssig = body[sub:sub+4].decode()
sln = struct.unpack('<H', body[sub+4:sub+6])[0]
vals = struct.unpack('<ffffff', body[sub+6:sub+6+sln])
print(f'DATA x={vals[0]} y={vals[1]} z={vals[2]} rx={vals[3]} ry={vals[4]} rz={vals[5]}')
