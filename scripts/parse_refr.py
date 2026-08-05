import struct

# Parse REFR records from both ESP files
for esp_file in [r'C:\XboxGames\Starfield\Content\Data\SeydaNeen.esp', r'C:\XboxGames\Starfield\Content\Data\SeydaNeen2.esp']:
    print('='*60)
    print('File:', esp_file.split(chr(92))[-1])
    with open(esp_file, 'rb') as f:
        data = f.read()
    print('Size:', len(data))
    
    pos = 0
    while pos < len(data) - 8:
        rec = data[pos:pos+4]
        if rec == b'REFR':
            formid = struct.unpack_from('<I', data, pos+12)[0]
            data_size = struct.unpack_from('<I', data, pos+4)[0]
            flags = struct.unpack_from('<I', data, pos+8)[0]
            print('REFR at', pos, 'FormID:', hex(formid), 'flags:', hex(flags), 'size:', data_size)
            rec_data = data[pos+24:pos+24+data_size]
            
            # Parse subrecords
            rpos = 0
            while rpos < len(rec_data) - 4:
                sub = rec_data[rpos:rpos+4]
                if sub == b'NAME':
                    sub_size = struct.unpack_from('<I', rec_data, rpos+4)[0]
                    name = rec_data[rpos+8:rpos+8+sub_size-1]
                    print('  NAME:', name, 'size:', sub_size)
                    rpos += 8 + sub_size - 1
                elif sub == b'DATA':
                    sub_size = struct.unpack_from('<I', rec_data, rpos+4)[0]
                    if sub_size == 24:
                        x, y, z, rx, ry, rz = struct.unpack('6f', rec_data[rpos+8:rpos+8+24])
                        parent_ref = struct.unpack_from('<I', rec_data, rpos+32)[0]
                        ref_id = struct.unpack_from('<I', rec_data, rpos+36)[0]
                        print('  DATA: pos=(%.2f, %.2f, %.2f) rot=(%.2f, %.2f, %.2f)' % (x, y, z, rx, ry, rz))
                        print('  DATA: parent_ref=0x%08X ref_id=0x%08X' % (parent_ref, ref_id))
                    else:
                        print('  DATA: size=%d' % sub_size)
                    rpos += 8 + sub_size
                else:
                    rpos += 1
            pos += 24 + data_size
        else:
            pos += 1

