import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# Second STAT at 0x154
pos = 0x154
sig = data[pos:pos+4].decode()
size = struct.unpack('<I', data[pos+4:pos+8])[0]
flags = struct.unpack('<I', data[pos+8:pos+12])[0]
formid = struct.unpack('<I', data[pos+12:pos+16])[0]
print(f'0x{pos:x}: {sig} size={size} flags=0x{flags:08X} formid=0x{formid:08X}')
# subrecords start at pos+16
sub = pos+16
end = pos+16+size
while sub < end:
    ssig = data[sub:sub+4].decode('ascii', errors='replace')
    sln = struct.unpack('<H', data[sub+4:sub+6])[0]
    payload = data[sub+6:sub+6+sln]
    print(f'  {ssig} len={sln} payload={payload[:80]}')
    sub += 6 + sln
