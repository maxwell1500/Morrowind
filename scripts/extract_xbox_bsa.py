"""
Xbox/Game Pass Morrowind BSA Extractor
Parses the Xbox BSA format and extracts files.
"""
import struct
import os
import sys


def extract_xbox_bsa(bsa_path, output_dir):
    """Extract all files from an Xbox/Game Pass Morrowind BSA."""
    print(f"Opening: {bsa_path}")
    
    with open(bsa_path, 'rb') as f:
        data = f.read()
    
    filesize = len(data)
    print(f"File size: {filesize:,} bytes ({filesize/1024/1024:.1f} MB)")
    
    # Find all null-terminated strings that look like file paths
    file_paths = []
    i = 0
    while i < len(data) - 5:
        # Look for backslash (0x5C) which indicates a path
        if data[i] == 0x5C:  # backslash
            # Walk backwards to find start of string
            start = i
            while start > 0 and data[start - 1] >= 0x20 and data[start - 1] < 0x7F:
                start -= 1
            
            # Walk forwards to find end of string
            end = i
            while end < len(data) - 1 and data[end + 1] >= 0x20 and data[end + 1] < 0x7F:
                end += 1
            end += 1  # include the last char
            
            path = data[start:end].decode('ascii', errors='ignore')
            if len(path) > 5 and ('.' in path):
                file_paths.append((start, end, path))
                i = end
            else:
                i += 1
        else:
            i += 1
    
    print(f"Found {len(file_paths)} file paths")
    
    # Extract each file
    os.makedirs(output_dir, exist_ok=True)
    extracted = 0
    
    for idx, (start, end, path) in enumerate(file_paths):
        # Clean up path
        clean_path = path.replace('\\', '/')
        
        # The file data starts after the null terminator of the path string
        data_start = end + 1  # after the last character
        # But we need to skip any null bytes
        while data_start < len(data) and data[data_start] == 0:
            data_start += 1
        
        # Determine file size - read until next path or null sequence
        # For now, read a reasonable chunk and check for next path
        if idx + 1 < len(file_paths):
            next_start = file_paths[idx + 1][0]
            file_size = next_start - data_start
        else:
            file_size = min(1024 * 1024, filesize - data_start)  # last file, max 1MB
        
        if file_size <= 0 or file_size > 100 * 1024 * 1024:  # sanity check
            continue
        
        # Create output directory
        out_path = os.path.join(output_dir, clean_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        # Write file
        try:
            file_data = data[data_start:data_start + file_size]
            with open(out_path, 'wb') as f:
                f.write(file_data)
            extracted += 1
            
            if extracted % 500 == 0 or extracted <= 5:
                print(f"  [{extracted}] {clean_path} ({file_size:,} bytes)")
        except Exception as e:
            pass
        
        if idx % 2000 == 0 and idx > 0:
            print(f"  Processed {idx}/{len(file_paths)} paths...")
    
    print(f"\nExtracted {extracted} files to {output_dir}")
    return extracted


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_xbox_bsa.py <bsa_file> [output_dir]")
        sys.exit(1)
    
    bsa_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted"
    extract_xbox_bsa(bsa_file, output_dir)
