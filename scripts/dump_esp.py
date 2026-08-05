import struct
import zlib

def dump_record(data, offset):
    """Parse and dump a single ESP record."""
    if offset + 24 > len(data):
        return offset, None
    
    signature = data[offset:offset+4].decode('ascii', errors='replace')
    data_size = struct.unpack('<I', data[offset+4:offset+8])[0]
    flags = struct.unpack('<I', data[offset+8:offset+12])[0]
    form_id = struct.unpack('<I', data[offset+12:offset+16])[0]
    version = struct.unpack('<I', data[offset+16:offset+20])[0]
    unknown = struct.unpack('<I', data[offset+20:offset+24])[0]
    
    record_end = offset + 24 + data_size
    record_data = data[offset+24:record_end]
    
    print(f"\nRecord at offset {offset}:")
    print(f"  Signature: {signature}")
    print(f"  Data size: {data_size}")
    print(f"  Flags: {flags:#010x}")
    print(f"  FormID: {form_id:#010x}")
    print(f"  Version: {version:#010x}")
    print(f"  Unknown: {unknown:#010x}")
    
    if signature == 'REFR':
        dump_refr_data(record_data, record_end)
    elif signature == 'GRUP':
        dump_grup_data(record_data, record_end)
    
    return record_end, signature

def dump_refr_data(data, end_offset):
    """Parse REFR record subrecords."""
    pos = 0
    while pos + 8 <= len(data):
        sub_id = struct.unpack('<I', data[pos:pos+4])[0]
        sub_size = struct.unpack('<I', data[pos+4:pos+8])[0]
        sub_end = pos + 8 + sub_size
        
        if pos + 8 + sub_size > len(data):
            break
        
        print(f"  Subrecord: {struct.pack('<I', sub_id).decode('ascii', errors='replace')} ({sub_size} bytes)")
        
        if sub_id == 0x454d414e:  # NAME
            dump_name_subrecord(data[pos+8:sub_end])
        elif sub_id == 0x41544144:  # DATA
            dump_data_subrecord(data[pos+8:sub_end])
        elif sub_id == 0x4c435644:  # LCVD
            print(f"    LCVD (Level Cell Version Data)")
        elif sub_id == 0x52414544:  # READ
            print(f"    READ (Reference Data)")
        else:
            print(f"    Hex: {data[pos+8:sub_end+1].hex()}")
        
        pos = sub_end

def dump_name_subrecord(data):
    """Parse NAME subrecord (formID reference)."""
    if len(data) >= 4:
        form_id = struct.unpack('<I', data[:4])[0]
        print(f"    FormID: {form_id:#010x}")
        if len(data) > 4:
            print(f"    Extra bytes: {data[4:].hex()}")

def dump_data_subrecord(data):
    """Parse DATA subrecord (position/rotation)."""
    if len(data) >= 24:
        x, y, z, rx, ry, rz = struct.unpack('<6f', data[:24])
        print(f"    Position: ({x:.2f}, {y:.2f}, {z:.2f})")
        print(f"    Rotation: ({rx:.4f}, {ry:.4f}, {rz:.4f}) radians")
        print(f"    Rotation deg: ({rx*180/3.14159:.2f}, {ry*180/3.14159:.2f}, {rz*180/3.14159:.2f})")
        if len(data) > 24:
            print(f"    Extra bytes: {data[24:].hex()}")

def dump_grup_data(data, end_offset):
    """Parse GRUP record data."""
    if len(data) >= 8:
        group_type = struct.unpack('<I', data[4:8])[0]
        label = struct.unpack('<I', data[0:4])[0]
        print(f"  Group type: {group_type}")
        print(f"  Label: {label:#010x}")
    else:
        print(f"  Hex: {data.hex()}")

# Read and parse SeydaNeen2.esp
esp_path = 'C:/XboxGames/Starfield/Content/Data/SeydaNeen2.esp'
with open(esp_path, 'rb') as f:
    esp_data = f.read()

print(f"File size: {len(esp_data)} bytes")
print(f"Header (first 24 bytes): {esp_data[:24].hex()}")

offset = 0
records = []
while offset < len(esp_data):
    offset, sig = dump_record(esp_data, offset)
    if sig:
        records.append(sig)
    if offset >= len(esp_data):
        break

print(f"\n\nTotal records: {len(records)}")
print(f"Record types: {', '.join(records)}")
