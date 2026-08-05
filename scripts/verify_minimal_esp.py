import struct

with open(r'C:\Users\max\Projects\Morrowind\Data\SeydaNeen_Minimal.esp', 'rb') as f:
    data = f.read()

print(f'Size: {len(data)} bytes')

pos = 0
# TES4
sig = data[pos:pos+4].decode()
sz = struct.unpack_from('<I', data, pos+4)[0]
flags = struct.unpack_from('<I', data, pos+8)[0]
print(f'\nTES4 size={sz} flags=0x{flags:08X} ESM={bool(flags&1)} ESL={bool(flags&0x100)}')
pos += 24 + sz

# Parse GRUPs
while pos < len(data) - 4:
    sig = data[pos:pos+4].decode()
    if sig == 'GRUP':
        gs = struct.unpack_from('<I', data, pos+4)[0]
        label = data[pos+8:pos+12]
        gt = struct.unpack_from('<I', data, pos+12)[0]
        print(f'\nGRUP type={gt} @ {pos} size={gs}')
        
        if gt == 0:
            print(f'  Top-level label: {label}')
            pos += 24
            # Parse contents
            end = pos + gs - 24
            while pos < end:
                inner = data[pos:pos+4].decode(errors='replace')
                if inner == 'GRUP':
                    break
                isz = struct.unpack_from('<I', data, pos+4)[0]
                iflags = struct.unpack_from('<I', data, pos+8)[0]
                ifid = struct.unpack_from('<I', data, pos+12)[0]
                print(f'  {inner} FID=0x{ifid:08X} size={isz} flags=0x{iflags:08X}')
                
                if inner in ('STAT', 'WRLD', 'CELL', 'REFR'):
                    sp = pos + 24
                    while sp < pos + 24 + isz - 6:
                        ss = data[sp:sp+4].decode(errors='replace')
                        ssz = struct.unpack_from('<H', data, sp+4)[0]
                        if ss == 'EDID':
                            edid = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode()
                            print(f'    EDID: {edid}')
                        elif ss == 'MODL':
                            modl = data[sp+6:sp+6+ssz].rstrip(b'\x00').decode()
                            print(f'    MODL: {modl}')
                        elif ss == 'NAME':
                            ref = struct.unpack_from('<I', data, sp+6)[0]
                            print(f'    NAME: 0x{ref:08X}')
                        elif ss == 'DATA' and ssz == 24:
                            x,y,z,rx,ry,rz = struct.unpack_from('<6f', data, sp+6)
                            print(f'    DATA: ({x},{y},{z}) rot=({rx},{ry},{rz})')
                        elif ss == 'DATA' and ssz == 4:
                            v = struct.unpack_from('<I', data, sp+6)[0]
                            print(f'    DATA: 0x{v:08X}')
                        elif ss == 'XCLC':
                            gx,gy = struct.unpack_from('<ii', data, sp+6)
                            print(f'    XCLC: ({gx},{gy})')
                        elif ss == 'DNAM' and ssz == 8:
                            a,b = struct.unpack_from('<2f', data, sp+6)
                            print(f'    DNAM: ({a},{b})')
                        sp += 6 + ssz
                
                pos += 24 + isz
            pos = pos  # continue after inner records
        else:
            pos += gs
    else:
        print(f'Unexpected: {sig} @ {pos}')
        break

print(f'\nFinal pos: {pos}, file size: {len(data)}')
print('OK' if pos == len(data) else 'MISMATCH')
