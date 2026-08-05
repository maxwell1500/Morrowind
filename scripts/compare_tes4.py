import struct
for path in [r'C:\XboxGames\Starfield\Content\Data\Starfield.esm', r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp']:
    data = open(path, 'rb').read()[:32]
    print(path)
    print('hex:', data.hex())
    print('sig:', data[:4])
    print('size:', struct.unpack('<I', data[4:8])[0])
    print('flags:', hex(struct.unpack('<I', data[8:12])[0]))
    print('field 0x10-0x13:', data[0x10:0x14].hex())
    print('field 0x14-0x17:', data[0x14:0x18].hex())
    print('field 0x18-0x1b:', data[0x18:0x1c].hex())
    print()
