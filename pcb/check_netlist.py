"""Compare the schematic's exported netlist (sch.net) with design.py pin-to-net assignments."""
import re, design as D
t = open('sch.net', encoding='utf-8').read()
nets = {}
for blk in re.split(r'\(net\s+\(code', t)[1:]:
    name = re.search(r'\(name\s+"([^"]*)"', blk).group(1)
    for n in re.finditer(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"', blk):
        nets[(n.group(1), n.group(2))] = name
exp = {}
for ref, p in D.PARTS.items():
    for pin, net in p[7].items():
        if pin == "TAB": exp[(ref, "2")] = net
        elif pin == "LEAD": exp[(ref, "1")] = net; exp[(ref, "3")] = net
        else: exp[(ref, pin)] = net
bad = [(k, exp[k], nets.get(k)) for k in exp if nets.get(k) != exp[k]]
extra = [(k, nets[k]) for k in nets if k not in exp]
print('pins in design:', len(exp), '| pins in schematic netlist:', len(nets), '| mismatches:', bad[:8], '| extra:', extra[:8])
