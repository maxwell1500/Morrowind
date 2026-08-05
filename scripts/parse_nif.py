"""Parse Starfield NIF 20.2.0.7 structure."""
import struct
import sys

def parse_nif(path, max_blocks=20):
    with open(path, 'rb') as f:
        data = f.read()

    print(f"File: {path}")
    print(f"Size: {len(data)} bytes")

    # Header: 40 bytes version string + 4 bytes unknown
    version_str = data[:39].decode('ascii', errors='replace')
    print(f"Version string: {version_str!r}")
    # After header, there's a NIF 20.x header
    # 40-43: ?
    # 44-47: max string length?
    # 48-51: something
    # ...

    pos = 40
    # Look at unknown bytes
    print(f"Bytes 40-44: {data[40:44].hex()}")
    print(f"Bytes 44-48: {data[44:48].hex()}")
    print(f"Bytes 48-52: {data[48:52].hex()}")
    print(f"Bytes 52-56: {data[52:56].hex()}")

    # The NIF 20.x header has a "Block Type List" with a magic signature
    # Looking for 0x07 0x00 0x02 0x14 - this is constant
    # Then 0x01 0x0C = 3073 (probably max_string_length or something)
    # Then num_blocks
    # Then block types
    # Then num_roots
    # Then root indices
    # Then block data

    # Try to find the first length-prefixed string
    # Skip the first 40 bytes
    pos = 40
    # Look at the bytes right after
    print(f"\nAttempting to parse from offset 40...")
    for i in range(40, 100):
        print(f"@{i}: 0x{data[i]:02X} '{chr(data[i]) if 32 <= data[i] < 127 else '.'}'")

parse_nif(sys.argv[1] if len(sys.argv) > 1 else r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif")
