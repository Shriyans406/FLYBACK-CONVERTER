"""Stage 1 (run with KiCad's python): create the board, outline, slots and place every footprint.
Writes ACF_Flyback.kicad_pcb and pads.json (pad geometry for the router)."""
import json, os, sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
LIBS = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
mm = pcbnew.FromMM


def P(x, y):
    return pcbnew.VECTOR2I(mm(x + D.OX), mm(y + D.OY))


board = pcbnew.CreateEmptyBoard()
nets = {}
for name in D.NET_DOMAIN:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    nets[name] = ni


def rect(x0, y0, x1, y1, layer, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1))
    s.SetLayer(layer); s.SetWidth(mm(width))
    board.Add(s)


def text(s, x, y, size=1.5, layer=pcbnew.F_SilkS, rot=0, just="C"):
    t = pcbnew.PCB_TEXT(board)
    if just == "L":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15))
    if rot:
        t.SetTextAngleDegrees(rot)
    board.Add(t)


# outline + isolation slots
def seg(x0, y0, x1, y1, layer=pcbnew.Edge_Cuts):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1)); s.SetLayer(layer); s.SetWidth(mm(0.1))
    board.Add(s)


def arc(sx, sy, mx, my, ex, ey):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(P(sx, sy), P(mx, my), P(ex, ey)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
    board.Add(s)


W_, H_, R_ = D.BOARD_W, D.BOARD_H, D.CORNER_R
k = R_ * (1 - 0.70710678)                      # arc mid-point offset from the corner
seg(R_, 0, W_ - R_, 0); seg(W_, R_, W_, H_ - R_); seg(W_ - R_, H_, R_, H_); seg(0, H_ - R_, 0, R_)
arc(0, R_, k, k, R_, 0); arc(W_ - R_, 0, W_ - k, k, W_, R_)
arc(W_, H_ - R_, W_ - k, H_ - k, W_ - R_, H_); arc(R_, H_, k, H_ - k, 0, H_ - R_)
for s in D.SLOTS:
    rect(*s, pcbnew.Edge_Cuts)

pads_out = []
NC_PINS = {("U1", "15"): "unconnected-(U1-SYNC-Pad15)"}
for ref, (lib, name, value, anchor, x, y, rot, padnets, desc) in D.PARTS.items():
    fp = pcbnew.FootprintLoad(os.path.join(LIBS, lib + ".pretty"), name)
    if fp is None:
        raise SystemExit(f"footprint not found: {lib}:{name}")
    fp.SetReference(ref); fp.SetValue(value)
    fp.SetPath(pcbnew.KIID_PATH("/" + D.sym_uuid(ref)))
    fp.SetFPIDAsString(f"{lib}:{name}")
    fp.SetField("Description", desc)
    fp.SetPosition(P(0, 0)); fp.SetOrientationDegrees(rot)
    board.Add(fp)

    def kind(p):                       # TO-263-2 diode: tab vs leads
        return "TAB" if pcbnew.ToMM(max(p.GetSize().x, p.GetSize().y)) > 6 else "LEAD"

    numbered = [p for p in fp.Pads() if p.GetNumber() != ""]
    if anchor is not None:
        a = [p for p in numbered if p.GetNumber() == anchor or (anchor in ("TAB", "LEAD") and kind(p) == anchor)][0]
        off = a.GetPosition() - fp.GetPosition()
        fp.SetPosition(P(x, y) - off)
    else:
        fp.SetPosition(P(x, y))
    for p in numbered:
        key = p.GetNumber() if p.GetNumber() in padnets else kind(p) if ("TAB" in padnets) else None
        net = padnets.get(key)
        if net:
            p.SetNet(nets[net])
        elif (ref, p.GetNumber()) in NC_PINS:          # no-connect pin: same net name the schematic gives it
            ni = pcbnew.NETINFO_ITEM(board, NC_PINS[(ref, p.GetNumber())])
            board.Add(ni); p.SetNet(ni)
        tht = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        if net and not tht and max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)) > 6:
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)      # solid copper on heat-sink tabs
        bb = p.GetBoundingBox()
        pads_out.append(dict(ref=ref, num=p.GetNumber(), net=net, tht=bool(tht),
                             x0=pcbnew.ToMM(bb.GetLeft()) - D.OX, y0=pcbnew.ToMM(bb.GetTop()) - D.OY,
                             x1=pcbnew.ToMM(bb.GetRight()) - D.OX, y1=pcbnew.ToMM(bb.GetBottom()) - D.OY))

for i, (hx, hy) in enumerate(D.HOLES):
    fp = pcbnew.FootprintLoad(os.path.join(LIBS, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
    fp.SetReference(f"H{i+1}"); fp.SetValue("M3"); fp.SetPosition(P(hx, hy))
    fp.SetPath(pcbnew.KIID_PATH("/" + D.sym_uuid(f"H{i+1}")))
    fp.SetFPIDAsString("MountingHole:MountingHole_3.2mm_M3")
    fp.SetField("Description", "mounting hole")
    board.Add(fp)

# ---- board-only items: fiducials, legends, enclosure ----
BOARD_ONLY = pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
for i, (fx, fy) in enumerate(D.FIDUCIALS):
    fp = pcbnew.FootprintLoad(os.path.join(LIBS, "Fiducial.pretty"), "Fiducial_1mm_Mask2mm")
    fp.SetReference(f"FID{i+1}"); fp.SetValue("Fiducial"); fp.SetPosition(P(fx, fy)); fp.SetAttributes(BOARD_ONLY)
    fp.Reference().SetVisible(False)
    board.Add(fp)
    # router keep-out = the 2 mm solder-mask opening around the fiducial dot
    pads_out.append(dict(ref=f"FID{i+1}", num="", net=None, tht=False, x0=fx - 1.0, y0=fy - 1.0, x1=fx + 1.0, y1=fy + 1.0))
for s_, x_, y_, sz_, j_ in D.SILK:
    text(s_, x_, y_, sz_, just=j_)

E = D.ENC
m_ = E["gap"]
rect(-m_, -m_, D.BOARD_W + m_, D.BOARD_H + m_, pcbnew.Dwgs_User)
rect(-m_ - E["wall"], -m_ - E["wall"], D.BOARD_W + m_ + E["wall"], D.BOARD_H + m_ + E["wall"], pcbnew.Dwgs_User)
text("ENCLOSURE OUTLINE (inner / outer wall) - 3D model in enclosure/", D.BOARD_W / 2, -m_ - E["wall"] - 2, 1.2, layer=pcbnew.Dwgs_User)
for ref_, fname, show in (("ENC1", "ACF_enclosure_base.wrl", True), ("ENC2", "ACF_enclosure_lid.wrl", False)):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref_); fp.SetValue("Enclosure base" if show else "Enclosure lid")
    fp.SetPosition(P(0, 0)); fp.SetAttributes(BOARD_ONLY)
    fp.Reference().SetLayer(pcbnew.F_Fab); fp.Value().SetLayer(pcbnew.F_Fab)
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    mdl = pcbnew.FP_3DMODEL()
    mdl.m_Filename = "${KIPRJMOD}/enclosure/" + fname
    mdl.m_Show = show
    fp.Models().push_back(mdl)
    board.Add(fp)

# silkscreen notes
text("PRIMARY - HIGH VOLTAGE 400V DC / 1kV SWITCHING", 48, 96.5, 1.3)
text("SECONDARY 54V / 1A", 128, 96.5, 1.3)
text("ISOLATION BARRIER", 100, 5.5, 1.0)
text("ACF FLYBACK 400V->54V  rev A", 128, 64, 1.2)

out = os.path.join(HERE, "ACF_Flyback.kicad_pcb")
pcbnew.SaveBoard(out, board)
json.dump(pads_out, open(os.path.join(HERE, "pads.json"), "w"), indent=0)
print("saved", out, "footprints:", len(board.GetFootprints()), "pads:", len(pads_out))
for p in pads_out:
    if p["ref"] in ("T1", "Q1", "Q2", "U2", "D1", "U3", "U1", "J1", "C1"):
        print(p["ref"], p["num"], p["net"], round((p["x0"] + p["x1"]) / 2, 2), round((p["y0"] + p["y1"]) / 2, 2))
