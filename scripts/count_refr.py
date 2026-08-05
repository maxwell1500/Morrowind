import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
count = data.count(b'REFR')
print(f'REFR count: {count}')
# find positions
pos = 0
for i in range(min(count, 5)):
    pos = data.find(b'REFR', pos)
    print(f'  at 0x{pos:x}')
    pos += 4
