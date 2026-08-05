import struct, zlib, io
# generate test ESP with all STATs, all CELLs, but only first 10 REFRs per cell
# Actually let's generate from the existing script but limit REFRs
exec(open(r'C:\Users\max\Projects\Morrowind\scripts\generate_esp_full.py').read().replace('for refr in refrs_by_cell[cell_name]:', 'for refr in refrs_by_cell[cell_name][:3]:').replace('for refr in refrs_by_cell["Seyda Neen"]:', 'for refr in refrs_by_cell["Seyda Neen"][:3]:'))
# Wait exec won't work with OUTPUT_FILE. Instead, just modify script and run.
