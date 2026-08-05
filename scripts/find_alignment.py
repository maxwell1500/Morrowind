import struct

new = open(r'C:\Users\max\Projects\Morrowind\ex_nord_house_03.nif', 'rb').read()
old = open(r'C:\Users\max\Projects\Morrowind\ex_nord_house_03.nif_old', 'rb').read()

# First find where the OLD data starts aligning with NEW
# OLD is 23775, NEW is 24445, diff is 670
# We need to find the offset shift

# OLD offset X = NEW offset X + 670 (if everything before the inserted 670 bytes matches)
# Let me look at the first 50 bytes
for offset in [0, 40, 60, 100, 200, 240, 300]:
    if old[offset:offset+20] == new[offset+670:offset+690]:
        print(f'OLD@{offset} == NEW@{offset+670}')

# Find first alignment
for shift in [0, 1, 4, 8, 16, 32, 64, 100, 200, 300, 500, 670]:
    matches = 0
    for i in range(0, min(len(old), len(new)-shift), 1):
        if old[i] == new[i+shift]:
            matches += 1
    if matches > 100:
        print(f'Shift {shift}: {matches} matches')

# Look at where OLD data starts to match NEW at offset + 670
# That would be where the 670 bytes were inserted
for offset in range(40, 100):
    if old[offset:offset+20] == new[offset+670:offset+690]:
        print(f'\nInsertion at OLD@{offset} = NEW@{offset+670}')
        print(f'OLD @{offset}: {old[offset:offset+20].hex()}')
        print(f'NEW @{offset}: {new[offset:offset+20].hex()}')
        print(f'NEW @{offset+670}: {new[offset+670:offset+690].hex()}')
        break
