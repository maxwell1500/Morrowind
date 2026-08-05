"""Deep analysis of ImperialCity.esm CELL hierarchy."""
import struct

with open(r"C:\XboxGames\Starfield\Content\Data\ImperialCity.esm", "rb") as f:
    data = f.read()

def parse_grup(pos, depth=0):
    if pos + 24 > len(data):
        return pos
    
    sig = data[pos:pos+4]
    if sig != b"GRUP":
        return pos + 1
    
    total_size = struct.unpack("<I", data[pos+4:pos+8])[0]
    label = data[pos+8:pos+12]
    grup_type = struct.unpack("<I", data[pos+12:pos+16])[0]
    
    indent = "  " * depth
    label_hex = label.hex()
    label_int = struct.unpack("<I", label)[0]
    
    # Only print CELL-related GRUPs
    if depth > 0 or grup_type == 0:
        print(f"{indent}GRUP: label_hex={label_hex} label_int={label_int} type={grup_type} size={total_size}")
    
    content_start = pos + 24
    content_end = pos + total_size
    p = content_start
    
    while p < content_end:
        if p + 4 > len(data):
            break
        
        sig = data[p:p+4]
        
        if sig == b"GRUP":
            p = parse_grup(p, depth + 1)
        elif sig in [b"CELL", b"REFR", b"STAT", b"ARMO", b"DOOR", b"NPC_", b"CONT", b"WRLD"]:
            rec_size = struct.unpack("<I", data[p+4:p+8])[0]
            rec_flags = struct.unpack("<I", data[p+8:p+12])[0]
            rec_formid = struct.unpack("<I", data[p+12:p+16])[0]
            
            sig_str = sig.decode("ascii")
            print(f"{indent}  {sig_str}: size={rec_size} flags=0x{rec_flags:08X} formID=0x{rec_formid:08X}")
            
            rec_end = p + 16 + rec_size
            sub_p = p + 16
            while sub_p + 6 <= rec_end:
                sub_sig = data[sub_p:sub_p+4]
                sub_size = struct.unpack("<H", data[sub_p+4:sub_p+6])[0]
                if sub_sig == b"EDID":
                    edid = data[sub_p+6:sub_p+6+sub_size].decode("utf-8", errors="replace").rstrip("\x00")
                    print(f"{indent}    EDID: {edid}")
                    break
                sub_p += 6 + sub_size
            
            p += 16 + rec_size
        else:
            p += 1
    
    return content_end

# Skip TES4 header
tes4_size = struct.unpack("<I", data[4:8])[0]
pos = 20 + tes4_size

print("=== ImperialCity.esm - CELL Hierarchy ===")
while pos < len(data):
    if data[pos:pos+4] == b"GRUP":
        pos = parse_grup(pos)
    else:
        pos += 1
