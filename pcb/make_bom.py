"""Write fab/ACF_Flyback_BOM.csv from design.py (grouped by value + footprint)."""
import csv, collections, os
import design as D
os.makedirs('fab', exist_ok=True)
g = collections.OrderedDict()
for ref, (lib, fp, val, a, x, y, rot, nets, desc) in D.PARTS.items():
    if ref == "NT1":            # copper-only net tie, not a purchasable part
        continue
    g.setdefault((val, fp, desc), []).append(ref)
with open('fab/ACF_Flyback_BOM.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Qty', 'References', 'Value', 'Footprint', 'Description'])
    for (val, fp, desc), refs in g.items():
        w.writerow([len(refs), ' '.join(refs), val, fp, desc])
print('BOM written:', len(g), 'lines')
