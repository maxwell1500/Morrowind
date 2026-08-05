"""
Full Morrowind BSA Extractor
Extracts ALL file types from Morrowind BSA v102 archives.
Based on the format documentation from bsa-nif-extractor.
"""
import struct
import os
import sys
from pathlib import Path


def extract_morrowind_bsa(bsa_path, output_dir):
    """Extract all files from a Morrowind BSA v102 archive."""
    raw = Path(bsa_path).read_bytes()
    
    if len(raw) < 12:
        raise ValueError("File too small to be a valid Morrowind BSA")
    
    magic = struct.unpack_from("<I", raw, 0)[0]
    hash_offset = struct.unpack_from("<I", raw, 4)[0]
    file_count = struct.unpack_from("<I", raw, 8)[0]
    
    if magic != 0x00000100:
        raise ValueError(f"Not a Morrowind BSA (magic: 0x{magic:08X})")
    
    if file_count == 0:
        print(f"  Empty archive: {bsa_path}")
        return 0
    
    # Section offsets
    FILE_REC_BASE = 12
    NAME_OFF_BASE = FILE_REC_BASE + file_count * 8
    NAME_BLK_BASE = NAME_OFF_BASE + file_count * 4
    HASH_TBL_BASE = hash_offset + 12
    DATA_BASE = HASH_TBL_BASE + file_count * 8
    
    # Read file sizes and offsets
    sizes = []
    offsets = []
    for i in range(file_count):
        sz = struct.unpack_from("<I", raw, FILE_REC_BASE + i * 8)[0]
        off = struct.unpack_from("<I", raw, FILE_REC_BASE + i * 8 + 4)[0]
        sizes.append(sz)
        offsets.append(off)
    
    # Read name offsets
    name_offsets = []
    for i in range(file_count):
        no = struct.unpack_from("<I", raw, NAME_OFF_BASE + i * 4)[0]
        name_offsets.append(no)
    
    # Extract all files
    os.makedirs(output_dir, exist_ok=True)
    extracted = 0
    
    for i in range(file_count):
        # Get filename
        npos = NAME_BLK_BASE + name_offsets[i]
        try:
            end = raw.index(b"\x00", npos)
        except ValueError:
            continue
        
        filepath = raw[npos:end].decode("latin-1", errors="replace")
        
        # Get file data
        dpos = DATA_BASE + offsets[i]
        data = raw[dpos:dpos + sizes[i]]
        
        # Write file
        out_path = os.path.join(output_dir, filepath.replace('\\', '/'))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        with open(out_path, 'wb') as f:
            f.write(data)
        
        extracted += 1
        if extracted % 1000 == 0:
            print(f"  Extracted {extracted}/{file_count} files...")
    
    return extracted


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_mw_bsa.py <bsa_file_or_directory> [output_dir]")
        print("  If input is a directory, extracts all .bsa files found.")
        print("  If input is a file, extracts just that BSA.")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_mw"
    
    if os.path.isdir(input_path):
        # Find all BSA files
        bsa_files = list(Path(input_path).glob("*.bsa"))
        print(f"Found {len(bsa_files)} BSA files in {input_path}")
        
        total = 0
        for bsa in bsa_files:
            print(f"\nExtracting: {bsa.name}")
            count = extract_morrowind_bsa(str(bsa), output_dir)
            print(f"  Extracted {count} files")
            total += count
        
        print(f"\nTotal: {extracted} files from {len(bsa_files)} archives")
    else:
        print(f"Extracting: {input_path}")
        count = extract_morrowind_bsa(input_path, output_dir)
        print(f"Extracted {count} files")


if __name__ == "__main__":
    main()
