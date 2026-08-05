import struct

data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0x63a8
sig = data[pos:pos+4].decode('ascii')
size = struct.unpack('<I', data[pos+4:pos+8])[0]
flags = struct.unpack('<I', data[pos+8:pos+12])[0]
formid = struct.unpack('<I', data[pos+12:pos+16])[0]
print(f'WRLD record: sig={sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
rec = data[pos+16:pos+16+size]
print(f'First 300 bytes hex: {rec[:300].hex()}')
print(f'First 300 bytes repr: {repr(rec[:300])}')

# Also dump the subrecords
i = 0
while i < len(rec):
    if i + 6 > len(rec):
        break
    sub_sig = rec[i:i+4].decode('ascii', errors='replace')
    sub_len = struct.unpack('<H', rec[i+4:i+6])[0]
    sub_data = rec[i+6:i+6+sub_len]
    print(f'  subrecord {sub_sig} len={sub_len} data={repr(sub_data[:60])}')
    i += 6 + sub_len
