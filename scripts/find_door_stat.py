import csv, struct
data = open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen.esp', 'rb').read()
# Read the STAT group and find ex_nord_door_01 formID
pos = 24 + struct.unpack('<I', data[4:8])[0]
while pos < len(data):
    sig = data[pos:pos+4].decode('ascii', errors='replace')
    if sig == 'GRUP' and data[pos+8:pos+12] == b'STAT':
        inner = pos + 24
        gend = pos + struct.unpack('<I', data[pos+4:pos+8])[0]
        while inner < gend:
            if data[inner:inner+4] == b'STAT':
                size = struct.unpack('<I', data[inner+4:inner+8])[0]
                fid = struct.unpack('<I', data[inner+12:inner+16])[0]
                body = data[inner+24:inner+24+size]
                sub = 0
                while sub < len(body):
                    ssig = body[sub:sub+4].decode('ascii', errors='replace')
                    sln = struct.unpack('<H', body[sub+4:sub+6])[0]
                    if ssig == 'EDID':
                        edid = body[sub+6:sub+6+sln]
                        if edid == b'ex_nord_door_01\x00':
                            print(f'ex_nord_door_01 STAT formID = 0x{fid:08X}')
                        break
                    sub += 6 + sln
                inner += 24 + size
        break
    pos += struct.unpack('<I', data[pos+4:pos+8])[0]
