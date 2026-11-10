"""Generate ACF_Flyback.kicad_sch (+ ACF.kicad_sym, sym-lib-table, .kicad_pro) from design.py.

The schematic is "label style": every pin carries a global net label instead of drawn wires,
so it always matches the netlist the board was built from. Run with any Python 3.
"""
import json, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
NS = uuid.UUID("6f1d7c2e-0000-4000-8000-00000000acf0")


def uid(tag):
    return str(uuid.uuid5(NS, tag))


ROOT = uid("root-sheet")
FONT = "(effects (font (size 1.27 1.27)))"
HIDE = "(effects (font (size 1.27 1.27)) hide)"

# ------------------------------------------------------------------ symbol library
SYMS = {}      # name -> dict(body=str graphics, pins=[(num, name, x, y, angle)], prefix)


def pin_txt(num, name, x, y, ang, length=2.54):
    return (f'(pin passive line (at {x:.2f} {y:.2f} {ang}) (length {length}) '
            f'(name "{name}" {FONT}) (number "{num}" {FONT}))')


def two_pin(name, prefix, graphics):
    SYMS[name] = dict(prefix=prefix, graphics=graphics, hide_names=True,
                      pins=[("1", "~", 0, 3.81, 270), ("2", "~", 0, -3.81, 90)], plen=1.27)


def box(name, prefix, left, right, width=20.32):
    n = max(len(left), len(right), 1)
    h = n * 2.54 + 2.54
    top = (n - 1) * 1.27
    pins = []
    for i, (num, pname) in enumerate(left):
        pins.append((num, pname, -width / 2 - 2.54, top - i * 2.54, 0))
    for i, (num, pname) in enumerate(right):
        pins.append((num, pname, width / 2 + 2.54, top - i * 2.54, 180))
    g = (f'(rectangle (start {-width/2:.2f} {h/2:.2f}) (end {width/2:.2f} {-h/2:.2f}) '
         f'(stroke (width 0.254) (type default)) (fill (type background)))')
    SYMS[name] = dict(prefix=prefix, graphics=g, hide_names=False, pins=pins, plen=2.54, h=h, w=width)


def line(pts, w=0.254):
    return f'(polyline (pts {" ".join(f"(xy {x} {y})" for x, y in pts)}) (stroke (width {w}) (type default)) (fill (type none)))'


two_pin("R", "R", '(rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))')
two_pin("C", "C", line([(-2.032, 0.762), (2.032, 0.762)], 0.5) + line([(-2.032, -0.762), (2.032, -0.762)], 0.5)
        + line([(0, 2.54), (0, 0.762)]) + line([(0, -2.54), (0, -0.762)]))
two_pin("CP", "C", line([(-2.032, 0.762), (2.032, 0.762)], 0.5) + line([(-2.032, -0.762), (2.032, -0.762)], 0.5)
        + line([(0, 2.54), (0, 0.762)]) + line([(0, -2.54), (0, -0.762)])
        + line([(-2.3, 1.9), (-1.3, 1.9)]) + line([(-1.8, 2.4), (-1.8, 1.4)]))
two_pin("D", "D", line([(-1.27, -1.27), (1.27, -1.27), (0, 1.27), (-1.27, -1.27)]) + line([(-1.27, 1.27), (1.27, 1.27)])
        + line([(0, 2.54), (0, 1.27)]) + line([(0, -2.54), (0, -1.27)]))          # pin 1 = cathode (top)
two_pin("F", "F", '(rectangle (start -0.762 -2.54) (end 0.762 2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
        + line([(0, 2.54), (0, -2.54)]))
box("CONN2", "J", [("1", "1"), ("2", "2")], [], 10.16)
box("SiC_MOSFET_7pin", "Q", [("1", "G"), ("2", "KS")], [("8", "D")] + [(str(i), "S") for i in range(3, 8)])
box("LM5025", "U", [("1", "VIN"), ("2", "RAMP"), ("3", "CS1"), ("4", "CS2"), ("5", "TIME"), ("6", "REF"), ("7", "VCC"), ("8", "OUT_A")],
    [("16", "UVLO"), ("15", "SYNC"), ("14", "RT"), ("13", "COMP"), ("12", "SS"), ("11", "AGND"), ("10", "PGND"), ("9", "OUT_B")], 25.4)
box("UCC5350S", "U", [("1", "VCC1"), ("2", "IN+"), ("3", "IN-"), ("4", "GND1")], [("5", "VCC2"), ("6", "OUTH"), ("7", "OUTL"), ("8", "VEE2")], 25.4)
box("OPTO", "U", [("1", "A"), ("2", "K")], [("4", "C"), ("3", "E")])
box("TL431", "U", [("2", "REF")], [("1", "K"), ("3", "A")])
box("XFMR_ETD", "T", [(n, "PRI+") for n in ("1", "2", "3")] + [(n, "PRI_SW") for n in ("5", "6", "7")],
    [(n, "SEC+") for n in ("14", "13", "12")] + [(n, "SEC_RTN") for n in ("11", "10", "9", "8")], 25.4)
box("SCHOTTKY_TO263", "D", [("1", "A"), ("3", "A")], [("2", "K")])
box("NET_TIE", "NT", [("1", "1")], [("2", "2")], 10.16)
SYMS["HOLE"] = dict(prefix="H", graphics='(circle (center 0 0) (radius 1.27) (stroke (width 0.5) (type default)) (fill (type none)))',
                    hide_names=True, pins=[], plen=2.54)


def sym_def(name, lib_prefix):
    s = SYMS[name]
    hide = "(pin_numbers hide) (pin_names (offset 0) hide)" if s["hide_names"] else "(pin_names (offset 0.508))"
    pins = "\n      ".join(pin_txt(n, pn, x, y, a, s["plen"]) for n, pn, x, y, a in s["pins"])
    return f'''  (symbol "{lib_prefix}{name}" {hide} (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "{s["prefix"]}" (at 2.54 1.27 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{name}" (at 2.54 -1.27 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "" (at 0 0 0) {HIDE})
    (property "Datasheet" "" (at 0 0 0) {HIDE})
    (symbol "{name}_0_1" {s["graphics"]})
    (symbol "{name}_1_1"
      {pins})
  )'''


SYM_OF = {"R": "R", "C": "C", "NT": "NET_TIE", "F": "F", "J": "CONN2", "Q": "SiC_MOSFET_7pin", "T": "XFMR_ETD"}
SPECIAL = {"U1": "LM5025", "U2": "UCC5350S", "U3": "OPTO", "U4": "TL431", "D1": "SCHOTTKY_TO263", "D2": "D",
           "C1": "CP", "C14": "CP"}


def symbol_for(ref):
    if ref in SPECIAL:
        return SPECIAL[ref]
    if ref.startswith("NT"):
        return "NET_TIE"
    return SYM_OF[ref.rstrip("0123456789")]


# ------------------------------------------------------------------ sheet content
GROUPS = [
    ("1. HV input, fuse, bulk capacitor, bleeder, ground star point", 25, 30, ["J1", "F1", "C1", "C2", "R16", "R17", "NT1"]),
    ("2. Power stage: transformer, main switch Q1, active clamp Q2 + C3, current sense", 25, 150, ["T1", "Q1", "Q2", "C3", "R1"]),
    ("3. Isolated high-side (clamp) gate drive with bootstrap supply", 25, 290, ["U2", "C4", "R2", "R3", "D2", "C5"]),
    ("4. LM5025 active-clamp controller, UVLO / feed-forward dividers, bias input", 430, 30,
     ["U1", "J3", "R4", "R5", "R6", "R7", "R8", "R9", "C6", "C7", "C8", "C9", "C10", "C11", "C12",
      "R10", "R11", "R12", "R13", "R14", "R15"]),
    ("5. Secondary rectifier and output filter", 430, 230, ["D1", "J2", "C14", "C15"]),
    ("6. Isolated feedback: TL431 + optocoupler, Y capacitor", 430, 350, ["U3", "U4", "C13", "R18", "R19", "R20", "R21", "R22", "R23", "C16"]),
]
out = []
nc = []


def g(v):                       # snap to the 1.27 mm schematic grid
    return round(round(v / 1.27) * 1.27, 2)


def glabel(net, x, y, ang, tag):
    just = "right" if ang in (180, 270) else "left"
    out.append(f'  (global_label "{net}" (shape passive) (at {x:.2f} {y:.2f} {ang}) (effects (font (size 1.27 1.27)) (justify {just})) '
               f'(uuid "{uid("lbl" + tag)}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) {HIDE}))')


def place(ref, sx, sy, value, footprint, desc, padnets, in_bom=True):
    name = symbol_for(ref) if not ref.startswith("H") else "HOLE"
    s = SYMS[name]
    pins_txt = " ".join(f'(pin "{n}" (uuid "{uid(ref + "pin" + n)}"))' for n, *_ in s["pins"])
    out.append(f'''  (symbol (lib_id "ACF:{name}") (at {sx:.2f} {sy:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp no)
    (uuid "{uid("sym" + ref)}")
    (property "Reference" "{ref}" (at {sx + 2.54:.2f} {sy - s.get("h", 5.08) / 2 - 3.5:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{value}" (at {sx + 2.54:.2f} {sy - s.get("h", 5.08) / 2 - 1.5:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{footprint}" (at {sx:.2f} {sy:.2f} 0) {HIDE})
    (property "Datasheet" "~" (at {sx:.2f} {sy:.2f} 0) {HIDE})
    (property "Description" "{desc}" (at {sx:.2f} {sy:.2f} 0) {HIDE})
    {pins_txt}
    (instances (project "ACF_Flyback" (path "/{ROOT}" (reference "{ref}") (unit 1))))
  )''')
    for n, pn, px, py, a in s["pins"]:
        x, y = sx + px, sy - py
        net = padnets.get(n)
        if net is None and "TAB" in padnets:                 # D1: tab = pin 2, leads = pins 1 and 3
            net = padnets["TAB"] if n == "2" else padnets["LEAD"]
        if net is None:
            out.append(f'  (no_connect (at {x:.2f} {y:.2f}) (uuid "{uid("nc" + ref + n)}"))')
            continue
        ang = {0: 180, 180: 0, 270: 90, 90: 270}[a]          # label points away from the symbol body
        glabel(net, x, y, ang, ref + n)


for title, gx, gy, refs in GROUPS:
    out.append(f'  (text "{title}" (exclude_from_sim no) (at {gx} {gy - 8} 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid "{uid("t" + title)}"))')
    boxes = [r for r in refs if "h" in SYMS[symbol_for(r)]]
    small = [r for r in refs if r not in boxes]
    x = gx + 35; rowh = 0
    for r in boxes:
        s = SYMS[symbol_for(r)]
        lib, fp, value, a, px, py, rot, padnets, desc = D.PARTS[r]
        place(r, g(x), g(gy + 30), value, f"{lib}:{fp}", desc, padnets, in_bom=not r.startswith("NT"))
        x += s["w"] + 65; rowh = max(rowh, s["h"])
    y = gy + 30 + rowh / 2 + 40
    for i, r in enumerate(small):
        lib, fp, value, a, px, py, rot, padnets, desc = D.PARTS[r]
        place(r, g(gx + 15 + (i % 14) * 25.4), g(y + (i // 14) * 50.8), value, f"{lib}:{fp}", desc, padnets)
for i in range(4):
    place(f"H{i+1}", g(760 + i * 12.7), g(560), "M3", "MountingHole:MountingHole_3.2mm_M3", "mounting hole", {}, in_bom=False)

lib_syms = "\n".join(sym_def(n, "ACF:") for n in SYMS)
sch = f'''(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
  (uuid "{ROOT}")
  (paper "A1")
  (title_block (title "Active-Clamp Flyback 400 V -> 54 V / 1 A") (rev "A") (comment 1 "Generated from pcb/design.py - label-style schematic"))
  (lib_symbols
{lib_syms}
  )
{chr(10).join(out)}
  (sheet_instances (path "/" (page "1")))
)
'''
open(os.path.join(HERE, "ACF_Flyback.kicad_sch"), "w", encoding="utf-8").write(sch)
open(os.path.join(HERE, "ACF.kicad_sym"), "w", encoding="utf-8").write(
    '(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") (generator_version "8.0")\n'
    + "\n".join(sym_def(n, "") for n in SYMS) + "\n)\n")
open(os.path.join(HERE, "sym-lib-table"), "w", encoding="utf-8").write(
    '(sym_lib_table\n  (version 7)\n  (lib (name "ACF")(type "KiCad")(uri "${KIPRJMOD}/ACF.kicad_sym")(options "")(descr "Symbols for the ACF flyback"))\n)\n')
pro = os.path.join(HERE, "ACF_Flyback.kicad_pro")
if not os.path.exists(pro):
    json.dump({"meta": {"filename": "ACF_Flyback.kicad_pro", "version": 3}, "sheets": [[ROOT, "Root"]],
               "board": {}, "schematic": {}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}},
              open(pro, "w"), indent=2)
print("schematic written:", len(D.PARTS) + 4, "symbols")
