import struct

with open(r'C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_de_docks_center.nif', 'rb') as f:
    data = f.read()

print(f'File size: {len(data)} bytes')
print(f'Version: {data[24:64].decode("ascii", errors="ignore")}')

# Find block type strings
pos = 64
strings = []
while pos < len(data) - 4:
    length = struct.unpack_from('<I', data, pos)[0]
    if length > 100 or length < 1 or pos + 4 + length > len(data):
        break
    s = data[pos+4:pos+4+length]
    try:
        s.decode('ascii')
        strings.append(s.decode('ascii'))
        pos += 4 + length
        pos = (pos + 3) & ~3  # 4-byte align
    except:
        break

print('Block types:')
for s in strings:
    print(f'  {s}')

# Print hex dump of block type strings area
print(f'\nHex dump of block type strings (offset {64} to {64 + sum(4 + len(s) + ((4 - len(s) % 4) % 4) for s in strings)}):')
end_pos = 64
for s in strings:
    s_len = len(s)
    pad = (4 - s_len % 4) % 4
    hex_data = data[end_pos:end_pos + 4 + s_len + pad]
    print(f'  {hex_data.hex()}')
    end_pos += 4 + s_len + pad
