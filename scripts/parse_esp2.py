import struct

with open(r'C:\XboxGames\Starfield\Content\Data\Seyda_Neen2.esp', 'rb') as f:
    data = f.read()

print('ESP file size:', len(data), 'bytes')
pos = 0
while pos < len(data) - 8:
    rec = data[pos:pos+4]
    if rec == b'REFR':
        data_size = struct.unpack_from('<I', data, pos+4)[0]
        flags = struct.unpack_from('<I', data, pos+8)[0]
        formid = struct.unpack_from('<I', data, pos+12)[0]
        print(f'REFR at {pos}, FormID: 0x{formid:08X}, flags: 0x{flags:08X}, size: {data_size}')
        rec_data = data[pos+24:pos+min(48, pos+24+data_size)]
        print(f'  HEX: {rec_data.hex()}')
        # Parse REFR DATA subrecord - 6 floats
        if len(rec_data) >= 48:
            x, y, z, rx, ry, rz = struct.unpack('6f', rec_data[:24])
            parent_ref = struct.unpack_from('<I', rec_data, 24)[0]
            ref_id = struct.unpack_from('<I', rec_data, 28)[0]
            print(f'  pos: ({x:.2f}, {y:.2f}, {z:.2f})')
            print(f'  rot: ({rx:.4f}, {ry:.4f}, {rz:.4f})')
            print(f'  parent_ref: 0x{parent_ref:08X}, ref_id: 0x{ref_id:08X}')
        pos += 24 + data_size
    else:
        pos += 1
