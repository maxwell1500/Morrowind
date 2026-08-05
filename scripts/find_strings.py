import struct, re

path = r'C:\XboxGames\Starfield\Content\Data\meshes\FurnishedStarborn\Starborn_ShipModel01.nif'
with open(path, 'rb') as f:
    data = f.read()

# Find all string type references (these identify NIF block types)
# String refs in NIF 20.x use a length-prefixed string

# Find all positions where length-prefixed strings are - common offsets
def find_strings(buf, prefix=b''):
    results = []
    pos = 0
    while pos < len(buf) - 4:
        try:
            length = struct.unpack('<I', buf[pos:pos+4])[0]
            if 1 <= length <= 200:
                candidate = buf[pos+4:pos+4+length]
                if all(32 <= b < 127 for b in candidate.rstrip(b'\x00')):
                    s = candidate.rstrip(b'\x00').decode('ascii')
                    if prefix in s.lower() or s.startswith('bhk') or s.startswith('Ni') or s.startswith('BS'):
                        results.append((pos, length, s))
                    pos += 4 + length
                    continue
        except:
            pass
        pos += 1
    return results

results = find_strings(data)
for offset, length, s in results[:50]:
    print(f'  @{offset}: len={length} {s!r}')
