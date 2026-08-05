import struct

new = open(r'C:\Users\max\Projects\Morrowind\ex_nord_house_03.nif', 'rb').read()
old = open(r'C:\Users\max\Projects\Morrowind\ex_nord_house_03.nif_old', 'rb').read()

# Check shift 64: NEW[i+64] should match OLD[i] for most i
# Find first divergence
for i in range(40, 200):
    if old[i] != new[i+64]:
        print(f'First divergence at OLD@{i} vs NEW@{i+64}')
        print(f'OLD @ {i-4}..{i+4}: {old[max(0,i-4):i+8].hex()}')
        print(f'NEW @ {i-4}..{i+4}: {new[max(0,i-4+64):i+8+64].hex()}')
        break

# Then check what's at NEW[64] (where 670 bytes were inserted)
print(f'\nNEW @{64}..{64+670}:')
print(new[64:64+670].hex())
