import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0x63a8
size = struct.unpack('<I', data[pos+4:pos+8])[0]
rec = data[pos+16:pos+16+size]
# subrecords start after 8-byte prefix
sub = rec[8:]
# print all subrecords
i = 0
while i < len(sub):
    if i + 6 > len(sub): break
    sub_sig = sub[i:i+4].decode('ascii', errors='replace')
    sub_len = struct.unpack('<H', sub[i+4:i+6])[0]
    sub_data = sub[i+6:i+6+sub_len]
    print(f'{sub_sig} len={sub_len} data={sub_data.hex() if sub_len>16 else repr(sub_data)}')
    i += 6 + sub_len
