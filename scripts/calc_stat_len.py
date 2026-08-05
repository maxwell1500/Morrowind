import struct
edid = b'active_de_bed_30\x00'
obnd = struct.pack('<ffffff', -1.0, -1.0, -1.0, 1.0, 1.0, 1.0)
ody = struct.pack('<I', 0)
bfcb = b'BGSKeywordForm_Component\x00'
bfce = b''
modl = b'morrowind\active_de_bed_30.nif\x00'
print('EDID', len(edid), 4+2+len(edid))
print('OBND', len(obnd), 4+2+len(obnd))
print('ODTY', len(ody), 4+2+len(ody))
print('BFCB', len(bfcb), 4+2+len(bfcb))
print('BFCE', len(bfce), 4+2+len(bfce))
print('MODL', len(modl), 4+2+len(modl))
total = 4+2+len(edid)+4+2+len(obnd)+4+2+len(ody)+4+2+len(bfcb)+4+2+len(bfce)+4+2+len(modl)
print('sub_data total', total)
print('content with prefix', total + 8)
