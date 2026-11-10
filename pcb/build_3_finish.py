"""Stage 3 (run with KiCad's python): add routed tracks, vias, thermal vias, copper pours and
bottom-side keep-outs to the placed board, fill the zones, write the DRC rule file and save."""
import json, os, sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "ACF_Flyback.kicad_pcb")
mm = pcbnew.FromMM
LAYER = {0: pcbnew.F_Cu, 1: pcbnew.B_Cu}


def P(x, y):
    return pcbnew.VECTOR2I(mm(x + D.OX), mm(y + D.OY))


board = pcbnew.LoadBoard(PCB)
nets = {n: board.FindNet(n) for n in D.NET_DOMAIN}
routes = json.load(open(os.path.join(HERE, "routes.json")))
pads = json.load(open(os.path.join(HERE, "pads.json")))
if routes["failures"]:
    print("WARNING unrouted:", routes["failures"])

for net, l, x0, y0, x1, y1, w in routes["tracks"]:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1)); t.SetWidth(mm(w)); t.SetLayer(LAYER[l]); t.SetNet(nets[net])
    board.Add(t)


def via(net, x, y, dia, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    try:
        v.SetWidth(pcbnew.F_Cu, mm(dia))
    except TypeError:
        v.SetWidth(mm(dia))
    v.SetDrill(mm(drill)); v.SetNet(nets[net])
    board.Add(v)


for net, x, y in routes["vias"]:
    via(net, x, y, D.VIA_D, D.VIA_DRILL)
for net, cx, cy in D.THERMAL_VIAS:
    for dx in (-2.5, 0, 2.5):
        for dy in (-2.5, 0, 2.5):
            via(net, cx + dx, cy + dy, 0.6, 0.3)


def zone(net, layer, r, clearance, name, prio=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(LAYER[layer])
    if net:
        z.SetNet(nets[net])
    o = z.Outline(); o.NewOutline()
    for x, y in ((r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])):
        o.Append(mm(x + D.OX), mm(y + D.OY))
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.5)); z.SetThermalReliefSpokeWidth(mm(0.6))
    # thermal relief on THT pads, solid on SMD power pads; the narrow HV input rail is fully solid
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if net in ("HV_IN", "HVDC") else pcbnew.ZONE_CONNECTION_THT_THERMAL)
    z.SetAssignedPriority(prio)
    z.SetZoneName(name)
    board.Add(z)
    return z


for i, (net, layer, r, hard) in enumerate(D.POURS):
    dom = D.NET_DOMAIN[net]
    if hard and layer == 1:
        c = 3.0 if dom in ("SWD", "VCL") else 0.5      # heat-spreading islands under the tabs
        zone(net, layer, r, c, f"{net}_island_{i}", prio=40 + i)
    elif hard:
        zone(net, layer, r, 0.3, f"{net}_pour_{i}", prio=20 + i)
    else:
        zone(net, layer, r, 0.3, f"{net}_plane_{i}", prio=i - 14)

# Bottom-side keep-outs: stop the ground planes creeping up to high-voltage through-hole pads
islands = [(n, r) for n, l, r, h in D.POURS if l == 1 and h]
nk = 0
for p in pads:
    if not (p["tht"] and p["net"]):
        continue
    dom = D.NET_DOMAIN[p["net"]]
    if dom not in ("HVDC", "HVMID", "SWD", "VCL"):
        continue
    cx, cy = (p["x0"] + p["x1"]) / 2, (p["y0"] + p["y1"]) / 2
    if any(n == p["net"] and r[0] <= cx <= r[2] and r[1] <= cy <= r[3] for n, r in islands):
        continue
    c = D.clearance(p["net"], "PGND") + 0.05
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayer(pcbnew.B_Cu)
    for fn, val in (("SetDoNotAllowZoneFills", True), ("SetDoNotAllowCopperPour", True), ("SetDoNotAllowTracks", False),
                    ("SetDoNotAllowVias", False), ("SetDoNotAllowPads", False), ("SetDoNotAllowFootprints", False)):
        if hasattr(z, fn):
            getattr(z, fn)(val)
    o = z.Outline(); o.NewOutline()
    for x, y in ((p["x0"] - c, p["y0"] - c), (p["x1"] + c, p["y0"] - c), (p["x1"] + c, p["y1"] + c), (p["x0"] - c, p["y1"] + c)):
        o.Append(mm(x + D.OX), mm(y + D.OY))
    z.SetZoneName(f"HV_keepout_{p['ref']}_{p['num']}")
    board.Add(z); nk += 1

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
print("tracks", len(routes["tracks"]), "vias", len(routes["vias"]) + 9 * len(D.THERMAL_VIAS), "zones", len(D.POURS), "keepouts", nk)


# ---- custom design rules (creepage / clearance by voltage domain) ----
def member(side, dom_list):
    names = [n for d in dom_list for n in D.DOMAINS[d]]
    return "(" + " || ".join(f"{side}.NetName == '{n}'" for n in names) + ")"


padpad = "(A.Type == 'Pad' && B.Type == 'Pad')"
rules = ["(version 1)", ""]


def rule(name, cond, dist):
    rules.append(f'(rule "{name}"\n  (condition "{cond}")\n  (constraint clearance (min {dist}mm)))\n')


LV = ["PRI_LV"]
rule("hvmid_to_lv", f"{member('A', ['HVMID'])} && {member('B', LV)}", 0.95)
rule("hvdc_to_lv_copper", f"{member('A', ['HVDC'])} && {member('B', LV)} && !{padpad}", 2.45)
rule("hvdc_to_lv_pads", f"{member('A', ['HVDC'])} && {member('B', LV)} && {padpad}", 1.5)
for dom, others in (("SWD", ["PRI_LV", "HVDC", "HVMID", "VCL"]), ("VCL", ["PRI_LV", "HVDC", "HVMID"])):
    rule(f"{dom.lower()}_1kV_copper", f"{member('A', [dom])} && {member('B', others)} && !{padpad}", 2.95)
    rule(f"{dom.lower()}_1kV_pads", f"{member('A', [dom])} && {member('B', others)} && {padpad}", 2.0)
rule("primary_secondary_isolation", f"{member('A', ['SEC'])} && {member('B', ['PRI_LV', 'HVDC', 'HVMID', 'SWD', 'VCL'])}", 7.9)
open(os.path.join(HERE, "ACF_Flyback.kicad_dru"), "w").write("\n".join(rules))
print("rules written")
