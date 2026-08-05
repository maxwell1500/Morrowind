"""Generate minimal valid Starfield ESP for testing."""
import os
import struct
import io

OUTPUT_DIR = r"C:\Users\max\Projects\Morrowind\Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SeydaNeen.esp")

def write_subrecord(buf, sig, data):
    buf.write(sig.encode("ascii"))
    buf.write(struct.pack("<H", len(data)))
    buf.write(data)

def main():
    buf = io.BytesIO()
    
    # TES4 header
    buf.write(b"TES4")
    data_size_pos = buf.tell()
    buf.write(struct.pack("<I", 0))  # data size placeholder
    buf.write(struct.pack("<I", 0))  # flags = 0
    
    subrecord_start = buf.tell()
    
    # MAST - master files
    write_subrecord(buf, "MAST", b"Starfield.esm\x00")
    write_subrecord(buf, "MAST", b"TheElderStarSystem Magnus.esm\x00")
    
    # Fix data size
    data_size = buf.tell() - subrecord_start
    buf.seek(data_size_pos)
    buf.write(struct.pack("<I", data_size))
    buf.seek(0, 2)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(buf.getvalue())
    
    print(f"Created {OUTPUT_FILE}")
    print(f"Size: {buf.tell()} bytes")

if __name__ == "__main__":
    main()
