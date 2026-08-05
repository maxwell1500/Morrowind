import struct
import os

def read_dds_header(path):
    with open(path, 'rb') as f:
        magic = f.read(4)
        if magic != b'DDS ':
            return None
        header = f.read(124)
    
    # Parse header (offsets relative to start of header, which is after "DDS " magic)
    h_size = struct.unpack('<I', header[0:4])[0]     # Header size (should be 124)
    h_flags = struct.unpack('<I', header[4:8])[0]     # Header flags
    h_height = struct.unpack('<I', header[8:12])[0]   # Height
    h_width = struct.unpack('<I', header[12:16])[0]   # Width
    h_pitch = struct.unpack('<I', header[16:20])[0]   # Pitch/linear size
    h_depth = struct.unpack('<I', header[20:24])[0]   # Depth
    h_mips = struct.unpack('<I', header[24:28])[0]    # Mip count
    
    # Pixel format starts at offset 72 in header
    pf_size = struct.unpack('<I', header[72:76])[0]
    pf_flags = struct.unpack('<I', header[76:80])[0]
    pf_fourcc = header[80:84]
    pf_rgb = struct.unpack('<I', header[84:88])[0]
    pf_rmask = struct.unpack('<I', header[88:92])[0]
    pf_gmask = struct.unpack('<I', header[92:96])[0]
    pf_bmask = struct.unpack('<I', header[96:100])[0]
    pf_amask = struct.unpack('<I', header[100:104])[0]
    
    fourcc_str = pf_fourcc.decode('ascii', errors='replace')
    return {
        'width': h_width, 'height': h_height, 'mips': h_mips,
        'fourcc': fourcc_str, 'pf_flags': pf_flags, 'pf_rgb': pf_rgb,
        'size': os.path.getsize(path)
    }

# Check Morrowind textures
print("=== Morrowind Textures ===")
tex_dir = r"C:\Users\max\Projects\Morrowind\raw_assets\Morrowind_Full\textures"
targets = ['tx_wood_brown_posts_02', 'tx_bc_bark_01', 'tx_bc_fern_01', 'tx_bc_grass_01', 'tx_door_wood_01']
for t in targets:
    path = os.path.join(tex_dir, t + '.dds')
    if os.path.exists(path):
        info = read_dds_header(path)
        print(f"  {t}: {info['width']}x{info['height']}, {info['mips']} mips, fourcc={repr(info['fourcc'])}, pf_flags={info['pf_flags']:#x}, {info['size']} bytes")
    else:
        print(f"  {t}: NOT FOUND")

# Check Starfield textures
print("\n=== Starfield Textures ===")
sf_dir = r"C:\XboxGames\Starfield\Content\Data\textures"
count = 0
for root, dirs, files in os.walk(sf_dir):
    for f in files:
        if f.endswith('.dds') or f.endswith('.DDS'):
            path = os.path.join(root, f)
            info = read_dds_header(path)
            if info and info['width'] > 0 and info['height'] > 0:
                print(f"  {f}: {info['width']}x{info['height']}, {info['mips']} mips, fourcc={repr(info['fourcc'])}, pf_flags={info['pf_flags']:#x}, {info['size']} bytes")
                count += 1
                if count >= 5:
                    break
    if count >= 5:
        break
