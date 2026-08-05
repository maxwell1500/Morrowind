import re
src = open(r'C:\Users\max\Projects\Morrowind\scripts\generate_esp_full.py').read()
# Replace exterior REFR loop with empty loop
src2 = src.replace('for refr in refrs_by_cell["Seyda Neen"]:', 'for refr in []:')
# Save as temp script
open(r'C:\Users\max\Projects\Morrowind\scripts\generate_test_no_exterior_refr.py', 'w').write(src2)
print('Created temp script with no exterior REFRs')
