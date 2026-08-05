import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 24 + struct.unpack('<I', data[4:8])[0]
count = 0
while pos < len(data) - 24 and count < 20:
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP':
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
        label = data[pos+8:pos+12]
        print('GRUP type=%d label=%s size=%d' % (gtype, label, size))
        pos += size
    else:
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        print('Record %s size=%d' % (sig, size))
        pos += 24 + size
    count += 1
