import struct
path = r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif"
with open(path, 'rb') as f:
    data = f.read()

# Look at bytes 60-100 in detail
print('Bytes 52-100:')
for i in range(52, 100):
    c = chr(data[i]) if 32 <= data[i] < 127 else '.'
    print(f'  @{i:3d}: 0x{data[i]:02X} {c}')
