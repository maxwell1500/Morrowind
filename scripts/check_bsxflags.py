"""Compare BSXFlags and other extra data between NIFs."""
import struct
import re

paths = [
    (r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind\ex_nord_house_03.nif", "OUR HOUSE"),
    (r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_BuiltInKitchenette01.nif", "KITCHEN"),
    (r"C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_StorageCasing01.nif", "STORAGE"),
]

for path, label in paths:
    with open(path, 'rb') as f:
        data = f.read()
    print(f"\n=== {label} ({len(data)} bytes) ===")

    # Look for BSXFlags
    for marker in [b'BSXFlags', b'BSXFlag', b'BSBehaviorGraphExtraData', b'NiStringExtraData']:
        p = data.find(marker)
        if p != -1:
            # Read 4 bytes before for length
            if p >= 4:
                length = struct.unpack('<I', data[p-4:p])[0] if p > 4 else 0
            else:
                length = -1
            print(f"  {marker!r} found at offset {p}, len={length}")
            # Show next 20 bytes
            print(f"    next bytes: {data[p:p+30].hex()}")
