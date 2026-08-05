import struct
data = open(r'C:\XboxGames\Starfield\Content\Data\ImperialCity.esm', 'rb').read()
pos = 0x6316
print('Children group header:', data[pos:pos+24].hex())
size = struct.unpack('<I', data[pos+4:pos+8])[0]
label = data[pos+8:pos+12]
gtype = struct.unpack('<I', data[pos+12:pos+16])[0]
print(f'label={label.hex()} type={gtype} size={size}')
inner = pos + 24
end = pos + size
print('First items in children group:')
count = 0
while inner < end and count < 5:
    sig = data[inner:inner+4]
    if sig == b'GRUP':
        sz = struct.unpack('<I', data[inner+4:inner+8])[0]
        lb = data[inner+8:inner+12]
        tp = struct.unpack('<I', data[inner+12:inner+16])[0]
        print(f'  GRUP label={lb.hex()} type={tp} size={sz}')
        inner += sz
    else:
        sz = struct.unpack('<I', data[inner+4:inner+8])[0]
        print(f'  RECORD {sig} size={sz}')
        inner += 16 + sz
    count += 1
