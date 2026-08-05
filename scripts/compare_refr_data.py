import struct

# Read our ESP
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# Find first REFR in WRLD group
pos = 0
our_refr_data = None
while pos < len(data) - 24:
    if data[pos:pos+4] == b'REFR':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        body = data[pos+24:pos+24+size]
        sub = 0
        while sub < len(body):
            ssig = body[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            sdata = body[sub+6:sub+6+sln]
            if ssig == 'DATA':
                our_refr_data = sdata
                print('Our REFR DATA: len=%d hex=%s' % (sln, sdata.hex()))
                vals = struct.unpack('<ffffff', sdata)
                print('  Values: x=%.2f y=%.2f z=%.2f rx=%.2f ry=%.2f rz=%.2f' % vals)
                break
            sub += 6 + sln
        break
    pos += 1

# Read ImperialCity REFR DATA
print()
ic_data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0
while pos < len(ic_data) - 24:
    if ic_data[pos:pos+4] == b'REFR':
        size = struct.unpack('<I', ic_data[pos+4:pos+8])[0]
        flags = struct.unpack('<I', ic_data[pos+8:pos+12])[0]
        body = ic_data[pos+24:pos+24+size]
        sub = 0
        while sub < len(body):
            ssig = body[sub:sub+4].decode('ascii', errors='replace')
            sln = struct.unpack('<H', body[sub+4:sub+6])[0]
            sdata = body[sub+6:sub+6+sln]
            if ssig == 'DATA':
                print('ImperialCity REFR DATA: len=%d hex=%s' % (sln, sdata.hex()))
                if sln == 24:
                    vals = struct.unpack('<ffffff', sdata)
                    print('  Values: x=%.2f y=%.2f z=%.2f rx=%.2f ry=%.2f rz=%.2f' % vals)
                else:
                    print('  (unexpected length)')
                break
            sub += 6 + sln
        break
    pos += 1
