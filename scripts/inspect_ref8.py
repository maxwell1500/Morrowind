import csv
rows = list(csv.DictReader(open(r'C:\Users\max\Projects\Morrowind\converted_assets\placement\seyda_neen_all_placements.csv')))
exterior = [r for r in rows if r['cell'] == 'Seyda Neen']
ref = exterior[8]  # index 8 is the 8th element, but our slices were 6:7 etc. Wait our first 6 were indices 0-5, ref 7 is index 6, ref 8 is index 7? Actually the user said ref #7 is index 6? Hmm.
print('Ref at index 8:', ref)
# Actually we need to clarify: our slices [6:7] means indices 6 (7th ref). The user called it ref #7. So index 7 is ref #8.
ref = exterior[7]
print('Ref at index 7 (#8):', ref)
