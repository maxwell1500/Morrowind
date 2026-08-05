import struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
tes4_size = struct.unpack('<I', data[4:8])[0]
pos = 24
end = pos + tes4_size
while pos < end:
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    ln = struct.unpack('<H', data[pos+4:pos+6])[0]
    if sig == 'HEDR':
        version, num_records, next_id = struct.unpack('<fII', data[pos+6:pos+6+ln])
        print(f'HEDR: version={version} num_records={num_records} next_id=0x{next_id:08X}')
        break
    pos += 6 + ln
