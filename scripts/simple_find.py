import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\Starfield.esm', 'rb').read()
for i in range(100):
    pos = data.find(b'WRLD')
    print('found', pos)
    break
print('file size', len(data))
