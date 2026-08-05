import re
src = open(r'C:\Users\max\Projects\Morrowind\scripts\generate_esp_full.py').read()
# Replace exterior REFR loop to only include first N
src2 = src.replace(
    'for refr in refrs_by_cell["Seyda Neen"]:',
    'EXTERIOR_REFR_LIMIT = 100\nfor refr in refrs_by_cell["Seyda Neen"][:EXTERIOR_REFR_LIMIT]:'
)
open(r'C:\Users\max\Projects\Morrowind\scripts\generate_test_exterior_limit.py', 'w').write(src2)
print('Created generator with EXTERIOR_REFR_LIMIT')
