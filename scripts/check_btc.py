import struct

with open(r'C:\XboxGames\Starfield\Content\Data\Terrain\AutoSaveDEFAULT\Morrowind\cell_0_0.btc', 'rb') as f:
    data = f.read()

print(f'BTC size: {len(data)} bytes')
print(f'Magic: {data[0:4]}')
ver = struct.unpack_from('<I', data, 4)[0]
print(f'Version: {ver}')

data_size = len(data) - 8
print(f'Data size: {data_size}')
print(f'Expected for 128x128*2*2 = {128*128*2*2}')
print(f'Extra: {data_size - 128*128*2*2}')

# Check what's in the extra 32 bytes at the end
extra_start = 8 + 128*128*2*2
extra = data[extra_start:]
print(f'\nExtra bytes ({len(extra)}) at offset {extra_start}:')
print(f'Hex: {extra.hex()}')
vals = [struct.unpack_from('<I', extra, i*4)[0] for i in range(len(extra)//4)]
print(f'As uint32: {vals}')

# Also check: maybe the format is different
# Check if heights and textures are interleaved or sequential
# Read a few height values
print(f'\nFirst 10 height values (offset 8):')
for i in range(10):
    h = struct.unpack_from('<H', data, 8 + i*2)[0]
    print(f'  [{i}] = {h}')

print(f'\nFirst 10 texture values (offset 8 + 32768):')
for i in range(10):
    t = struct.unpack_from('<H', data, 8 + 32768 + i*2)[0]
    print(f'  [{i}] = {t}')
