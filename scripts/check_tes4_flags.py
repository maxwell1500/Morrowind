import struct
for path in [r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', r'C:\XboxGames\Starfield\Content\Data\Starfield.esm']:
    data = open(path, 'rb').read()[:24]
    print(path)
    print('hex', data.hex())
    print('flags', hex(struct.unpack('<I', data[8:12])[0]))
    print()
