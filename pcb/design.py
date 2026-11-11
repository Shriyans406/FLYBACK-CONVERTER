"""Shared design data for the active-clamp flyback PCB (pure Python, no KiCad imports).

Coordinates are board-local millimetres: x to the right, y down, origin at the
top-left board corner. OX/OY shift them onto the KiCad sheet.
"""
OX, OY = 30.0, 30.0
BOARD_W, BOARD_H = 155.0, 100.0

# Isolation barrier: no copper between these x values (primary left, secondary right)
BARRIER_X0, BARRIER_X1 = 96.05, 104.25
SLOTS = [(99.2, 16.0, 100.8, 54.0), (99.2, 58.0, 100.8, 92.0)]   # milled slots (x0,y0,x1,y1)
HOLES = [(5, 5), (150, 5), (5, 95), (150, 95)]                    # M3 mounting holes

DOMAINS = {
    "PRI_LV": ["PGND", "AGND", "VCC", "OUTA", "OUTB", "G1", "CS", "CSF", "REF5", "RT",
               "TIME", "SS", "COMP", "RAMP", "UVLO", "LEDA", "LB"],
    "HVDC":   ["HV_IN", "HVDC", "UV1", "FF1", "LH1"],
    "HVMID":  ["UV2", "FF2", "BL1", "LH2"],          # divider mid-points, <= 200 V
    "SWD":    ["SW", "G2", "G2R", "VB"],
    "VCL":    ["VCL"],
    "SEC":    ["SEC_A", "VOUT", "SGND", "FBM", "FB", "KA", "OPA", "CMP1", "LO1"],
}
NET_DOMAIN = {n: d for d, ns in DOMAINS.items() for n in ns}


def clearance(a, b):
    """Required copper spacing in mm between two different nets (tracks / pours)."""
    if a == b:
        return 0.0
    da, db = NET_DOMAIN[a], NET_DOMAIN[b]
    if da == db:
        return 0.6 if da in ("HVDC", "HVMID") else 0.2
    pair = {da, db}
    if "SEC" in pair:
        return 8.0
    if "SWD" in pair or "VCL" in pair:
        return 3.0
    if pair == {"HVDC", "HVMID"}:
        return 0.6
    if "HVMID" in pair:
        return 1.0        # divider mid-points <-> primary low-voltage
    return 2.5            # HVDC <-> primary low-voltage


TRACK_W = {"VCC": 0.5, "OUTA": 0.5, "OUTB": 0.4, "G1": 0.5, "G2": 0.5, "G2R": 0.5, "VB": 0.5,
           "SW": 0.5, "CS": 0.8, "PGND": 0.6, "AGND": 0.4, "SGND": 0.5, "VOUT": 0.5,
           "HVDC": 0.6, "HV_IN": 1.0, "VCL": 1.0, "SEC_A": 1.0}
DEFAULT_W = 0.25
VIA_D, VIA_DRILL = 0.8, 0.4
TOP_ONLY_DOMAINS = {"HVDC", "HVMID", "SWD", "VCL"}
NARROW_REFS = {"U1": 0.25}                     # neck tracks down at fine-pitch parts      # never routed on the bottom layer

F, B = 0, 1
# Copper pours: (net, layer, (x0,y0,x1,y1), hard). "hard" pours are fixed-shape power
# polygons that other nets must route around; "soft" pours are the bottom ground planes.
POURS = [
    ("HV_IN", F, (4.7, 10.6, 22.3, 13.2), True),
    ("HVDC",  F, (29.6, 9.2, 90.5, 13.2), True),
    ("HVDC",  F, (84.6, 9.2, 89.4, 31.6), True),
    ("VCL",   F, (55.3, 31.0, 71.7, 41.4), True),
    ("SW",    F, (74.8, 31.5, 79.5, 38.6), True),
    ("SW",    F, (78.5, 38.5, 90.5, 56.5), True),
    ("SW",    F, (77.7, 56.4, 90.5, 68.0), True),
    ("SEC_A", F, (110.4, 17.6, 124.7, 32.1), True),
    ("VOUT",  F, (126.7, 8.8, 153.0, 31.2), True),
    ("SGND",  F, (106.0, 33.0, 147.3, 58.0), True),
    # bottom-side heat-spreading islands under the tab-mounted parts
    ("SW",    B, (83.0, 38.5, 90.5, 56.5), True),
    ("SW",    B, (78.0, 56.4, 90.5, 68.0), True),
    ("VCL",   B, (63.0, 31.0, 71.0, 41.0), True),
    ("VOUT",  B, (127.0, 17.0, 136.0, 27.0), True),
    # bottom ground planes
    ("PGND",  B, (1.5, 1.5, 96.0, 27.5), False),
    ("PGND",  B, (1.5, 27.0, 15.5, 98.5), False),
    ("PGND",  B, (54.5, 27.0, 96.0, 98.5), False),
    ("AGND",  B, (16.0, 28.0, 54.0, 98.0), False),
    ("SGND",  B, (104.3, 1.5, 153.5, 98.5), False),
]
# Thermal via arrays (net, centre x, centre y) - 3x3 grid, 2.5 mm pitch
THERMAL_VIAS = [("SW", 82.0, 62.0), ("VCL", 67.0, 36.0), ("VOUT", 131.5, 22.0)]

R0805 = ("Resistor_SMD", "R_0805_2012Metric")
R1206 = ("Resistor_SMD", "R_1206_3216Metric")
C0805 = ("Capacitor_SMD", "C_0805_2012Metric")
TO2637 = ("Package_TO_SOT_SMD", "TO-263-7_TabPin8")
LED0805 = ("LED_SMD", "LED_0805_2012Metric")
TPLOOP = ("TestPoint", "TestPoint_Loop_D2.50mm_Drill1.0mm")
TPPAD = ("TestPoint", "TestPoint_Pad_D2.0mm")

# ref: (lib, footprint, value, anchor pad or None(=footprint origin), x, y, rotation, {pad: net}, description / part)
PARTS = {
 "J1":   ("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal", "400V DC IN", "1", 6.0, 12, 270, {"1": "HV_IN", "2": "PGND"}, "Phoenix MKDS 3/2-5,08"),
 "F1":   ("Fuse", "Fuseholder_Clip-5x20mm_Keystone_3517_Inline_P23.11x6.76mm_D1.70mm_Horizontal", "T1A 500V", None, 14.1, 12, 0, {"1": "HV_IN", "2": "HVDC"}, "Keystone 3517 clips + 5x20 fuse"),
 "C1":   ("Capacitor_THT", "CP_Radial_D12.5mm_P5.00mm", "22u 450V", "1", 45.4, 12, 270, {"1": "HVDC", "2": "PGND"}, "bulk electrolytic"),
 "C2":   ("Capacitor_THT", "C_Rect_L13.0mm_W5.0mm_P10.00mm_FKS3_FKP3_MKS4", "100n 630V", "1", 70, 12, 270, {"1": "HVDC", "2": "PGND"}, "film, HF loop bypass"),
 "C3":   ("Capacitor_THT", "C_Rect_L31.5mm_W9.0mm_P27.50mm_MKS4", "470n 1kV", "1", 57, 12, 270, {"1": "HVDC", "2": "VCL"}, "film clamp capacitor"),
 "T1":   ("Transformer_THT", "Transformer_EPCOS_B66359A1013T_Horizontal", "25mH 10:1", "1", 87, 20, 270,
          {"1": "HVDC", "2": "HVDC", "3": "HVDC", "5": "SW", "6": "SW", "7": "SW",
           "14": "SEC_A", "13": "SEC_A", "12": "SEC_A", "11": "SGND", "10": "SGND", "9": "SGND", "8": "SGND"},
          "PLACEHOLDER ETD29 bobbin - see notes"),
 "Q1":   (*TO2637, "IMBF170R1K0M1", "8", 81.5, 62, 0, {"1": "G1", **{str(i): "CS" for i in range(2, 8)}, "8": "SW"}, "Infineon 1700V SiC, main switch"),
 "Q2":   (*TO2637, "IMBF170R1K0M1", "8", 67, 36, 180, {"1": "G2", **{str(i): "SW" for i in range(2, 8)}, "8": "VCL"}, "Infineon 1700V SiC, clamp switch"),
 "R1":   ("Resistor_SMD", "R_2512_6332Metric", "0R27 1W", None, 61.9, 66.5, 0, {"1": "PGND", "2": "CS"}, "current sense"),
 "U2":   ("Package_SO", "SOIC-8_7.5x5.85mm_P1.27mm", "UCC5350SBDWV", None, 63, 56.5, 90,
          {"1": "VCC", "2": "OUTB", "3": "PGND", "4": "PGND", "5": "VB", "6": "G2R", "7": "G2R", "8": "SW"}, "isolated high-side gate driver"),
 "C4":   (*C0805, "1u 25V", None, 67, 48.6, 0, {"1": "VB", "2": "SW"}, "bootstrap capacitor"),
 "R2":   (*R1206, "10R", None, 63, 47.5, 90, {"1": "G2R", "2": "G2"}, "Q2 gate resistor"),
 "R3":   (*R0805, "10k", None, 76.15, 43.5, 270, {"1": "G2", "2": "SW"}, "Q2 gate pull-down"),
 "D2":   ("Diode_THT", "D_DO-41_SOD81_P10.16mm_Horizontal", "STTH112", "1", 67.8, 53.5, 270, {"1": "VB", "2": "VCC"}, "1200V bootstrap diode"),
 "C5":   (*C0805, "100n", None, 56.8, 64.5, 270, {"1": "VCC", "2": "PGND"}, "U2 input decoupling"),
 "R4":   (*R0805, "10R", None, 58, 72, 0, {"1": "OUTA", "2": "G1"}, "Q1 gate resistor"),
 "R5":   (*R0805, "10k", None, 64, 72, 0, {"1": "G1", "2": "PGND"}, "Q1 gate pull-down"),
 "U1":   ("Package_SO", "TSSOP-16_4.4x5mm_P0.65mm", "LM5025", None, 46, 74, 90,
          {"1": "VCC", "2": "RAMP", "3": "CSF", "4": "CSF", "5": "TIME", "6": "REF5", "7": "VCC", "8": "OUTA",
           "9": "OUTB", "10": "PGND", "11": "AGND", "12": "SS", "13": "COMP", "14": "RT", "16": "UVLO"}, "active-clamp PWM controller"),
 "R6":   (*R0805, "22k", None, 34, 67, 0, {"1": "AGND", "2": "UVLO"}, "UVLO divider bottom"),
 "R7":   (*R0805, "680k", None, 38.5, 67, 0, {"1": "AGND", "2": "RT"}, "oscillator (10 kHz, see notes)"),
 "C6":   (*C0805, "100n", None, 38.5, 63, 0, {"1": "AGND", "2": "SS"}, "soft-start"),
 "C7":   (*C0805, "1n", None, 43, 63, 0, {"1": "AGND", "2": "COMP"}, "COMP noise filter"),
 "C8":   (*C0805, "1n", None, 34, 81, 0, {"1": "AGND", "2": "RAMP"}, "ramp capacitor"),
 "C9":   (*C0805, "220p", None, 38.5, 81, 0, {"1": "AGND", "2": "CSF"}, "current-sense filter"),
 "R8":   (*R0805, "160k", None, 43, 81, 0, {"1": "TIME", "2": "REF5"}, "dead-time set"),
 "C10":  (*C0805, "100n", None, 47.5, 81, 0, {"1": "REF5", "2": "AGND"}, "REF decoupling"),
 "R9":   (*R0805, "1k", None, 38.5, 85, 0, {"1": "CSF", "2": "CS"}, "current-sense filter"),
 "C11":  (*C0805, "1u 25V", None, 52.5, 77.5, 270, {"1": "VCC", "2": "PGND"}, "VCC decoupling"),
 "C12":  ("Capacitor_SMD", "C_1206_3216Metric", "10u 25V", None, 9, 80.5, 0, {"1": "VCC", "2": "PGND"}, "VCC bulk"),
 "J3":   ("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical", "12V BIAS", "1", 9, 84, 0, {"1": "VCC", "2": "PGND"}, "primary-referenced 12 V bias input"),
 "R10":  (*R1206, "1M", None, 27, 18.5, 90, {"2": "HVDC", "1": "UV1"}, "UVLO divider"),
 "R11":  (*R1206, "1M", None, 27, 36, 90, {"2": "UV1", "1": "UV2"}, "UVLO divider"),
 "R12":  (*R1206, "1M", None, 27, 55, 90, {"2": "UV2", "1": "UVLO"}, "UVLO divider"),
 "R13":  (*R1206, "1M", None, 21, 18.5, 90, {"2": "HVDC", "1": "FF1"}, "ramp feed-forward"),
 "R14":  (*R1206, "1M", None, 21, 36, 90, {"2": "FF1", "1": "FF2"}, "ramp feed-forward"),
 "R15":  (*R1206, "1M", None, 21, 55, 90, {"2": "FF2", "1": "RAMP"}, "ramp feed-forward"),
 "R16":  (*R1206, "470k", None, 36, 18.5, 90, {"2": "HVDC", "1": "BL1"}, "bulk bleeder"),
 "R17":  (*R1206, "470k", None, 36, 24, 90, {"2": "BL1", "1": "PGND"}, "bulk bleeder"),
 "NT1":  ("NetTie", "NetTie-2_SMD_Pad0.5mm", "AGND-PGND star", None, 45.4, 24.0, 0, {"1": "PGND", "2": "AGND"}, "single-point ground tie (not fitted, copper only)"),
 "C13":  ("Capacitor_THT", "C_Disc_D11.0mm_W5.0mm_P10.00mm", "2n2 Y1", "1", 95, 62, 0, {"1": "PGND", "2": "SGND"}, "Y1 safety capacitor"),
 "U3":   ("Package_DIP", "DIP-4_W10.16mm", "LTV-817M", "1", 105.2, 78, 180, {"1": "OPA", "2": "KA", "3": "AGND", "4": "COMP"}, "optocoupler, 10.16 mm lead form"),
 "D1":   ("Package_TO_SOT_SMD", "TO-263-2", "RB218NS150", "TAB", 131.5, 22, 0, {"TAB": "VOUT", "LEAD": "SEC_A"}, "150V 20A Schottky"),
 "C14":  ("Capacitor_THT", "CP_Radial_D12.5mm_P5.00mm", "180u 100V", "1", 144, 29.5, 270, {"1": "VOUT", "2": "SGND"}, "output electrolytic, low ESR"),
 "C15":  ("Capacitor_SMD", "C_1210_3225Metric", "1u 100V", None, 134, 32.2, 90, {"1": "SGND", "2": "VOUT"}, "output ceramic"),
 "J2":   ("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "54V OUT", "1", 147, 12, 270, {"1": "VOUT", "2": "SGND"}, "Phoenix MKDS 1,5/2-5,08"),
 "U4":   ("Package_TO_SOT_SMD", "SOT-23", "TL431", None, 116, 80, 0, {"1": "KA", "2": "FB", "3": "SGND"}, "shunt reference (check K/R/A pin order of chosen vendor)"),
 "R18":  (*R1206, "22k", None, 112, 71, 0, {"1": "OPA", "2": "VOUT"}, "opto LED feed"),
 "R19":  (*R0805, "1k", None, 110.5, 83, 0, {"1": "OPA", "2": "KA"}, "TL431 bias"),
 "R20":  (*R1206, "200k", None, 125, 71, 0, {"1": "VOUT", "2": "FBM"}, "feedback divider top"),
 "R21":  (*R0805, "6k2", None, 125, 75.5, 0, {"1": "FB", "2": "FBM"}, "feedback divider top"),
 "R22":  (*R0805, "10k", None, 125, 80, 0, {"1": "FB", "2": "SGND"}, "feedback divider bottom"),
 "C16":  (*C0805, "100n", None, 116, 86, 0, {"1": "KA", "2": "CMP1"}, "Type-II compensation"),
 "R23":  (*R0805, "10k", None, 121.5, 86, 0, {"1": "CMP1", "2": "FB"}, "Type-II compensation"),
 # ---- usability features (indicators and probe points; converter values unchanged) ----
 "R26":  (*R1206, "220k", None, 31.5, 18.5, 90, {"2": "HVDC", "1": "LH1"}, "HV-live LED dropper"),
 "R27":  (*R1206, "220k", None, 31.5, 30, 90, {"2": "LH1", "1": "LH2"}, "HV-live LED dropper"),
 "R28":  (*R1206, "220k", None, 31.5, 41.5, 90, {"2": "LH2", "1": "LEDA"}, "HV-live LED dropper"),
 "D3":   (*LED0805, "RED", None, 31.5, 48, 90, {"1": "PGND", "2": "LEDA"}, "HV LIVE indicator (bulk capacitor charged)"),
 "R25":  (*R0805, "4k7", None, 9, 76.5, 0, {"1": "LB", "2": "VCC"}, "bias LED resistor"),
 "D4":   (*LED0805, "YELLOW", None, 9, 72.5, 0, {"1": "PGND", "2": "LB"}, "12 V BIAS indicator"),
 "R24":  (*R1206, "27k", None, 140, 72, 0, {"1": "VOUT", "2": "LO1"}, "output LED resistor"),
 "D5":   (*LED0805, "GREEN", None, 140, 77, 0, {"1": "SGND", "2": "LO1"}, "OUTPUT ON indicator"),
 "TP1":  (*TPLOOP, "VOUT", None, 144, 84, 0, {"1": "VOUT"}, "probe loop, +54 V output"),
 "TP2":  (*TPLOOP, "SGND", None, 144, 90, 0, {"1": "SGND"}, "probe loop, output return"),
 "TP3":  (*TPPAD, "VCC", None, 4.5, 78, 0, {"1": "VCC"}, "probe pad, 12 V bias (primary side)"),
 "TP4":  (*TPLOOP, "PGND", None, 6, 62, 0, {"1": "PGND"}, "probe loop, primary ground"),
 "TP5":  (*TPPAD, "CS", None, 75, 74, 0, {"1": "CS"}, "probe pad, current sense (primary side)"),
 "TP6":  (*TPPAD, "GATE", None, 70, 74, 0, {"1": "G1"}, "probe pad, Q1 gate (primary side)"),
}

# Routing order: tight / critical nets first, long quiet ones last
NET_ORDER = ["G2R", "VB", "G2", "SW", "G1", "CS", "OUTA", "OUTB", "CSF", "HV_IN", "HVDC", "BL1",
             "UV1", "UV2", "FF1", "FF2", "VCL", "REF5", "TIME", "RT", "SS", "UVLO", "RAMP", "VCC",
             "SEC_A", "KA", "OPA", "FB", "FBM", "CMP1", "LH1", "LH2", "LEDA", "LB", "LO1", "VOUT", "COMP", "AGND", "PGND", "SGND"]


import uuid as _uuid
_NS = _uuid.UUID("6f1d7c2e-0000-4000-8000-00000000acf0")


def sym_uuid(ref):
    """Stable ID shared by a schematic symbol and its PCB footprint (links the two files)."""
    return str(_uuid.uuid5(_NS, "sym" + ref))


# ---------------------------------------------------------------- handling / assembly / enclosure
CORNER_R = 3.0                                              # rounded board corners (mm)
FIDUCIALS = [(11, 4), (139, 4), (11, 96)]                   # pick-and-place fiducials (board only)
# Silkscreen legends: (text, x, y, size, justify) - "L" left, "C" centre
SILK = [
    ("+400V", 1.5, 7.9, 1.0, "L"), ("GND", 1.5, 21.6, 1.0, "L"),
    ("+54V", 141.5, 7.9, 1.0, "L"), ("RTN", 141.5, 21.6, 1.0, "L"),
    ("T1A 500V", 29.5, 7.2, 1.0, "L"),
    ("12V BIAS  pin1 +  pin2 GND", 12.5, 85.3, 0.9, "L"),
    ("HV LIVE", 33.6, 48, 1.0, "L"), ("BIAS", 11.2, 72.5, 1.0, "L"), ("OUTPUT ON", 142.4, 77, 1.0, "L"),
    ("VOUT", 144, 81.4, 1.0, "C"), ("RTN", 140.2, 90, 1.0, "C"),
    ("VCC", 2.2, 80.6, 0.9, "L"), ("PGND", 8.4, 62, 1.0, "L"),
    ("CS", 75, 76.4, 0.9, "C"), ("GATE", 70, 76.4, 0.9, "C"),
    ("DANGER: WAIT FOR THE HV LIVE LED TO GO OUT BEFORE TOUCHING", 48, 92.8, 1.0, "C"),
    ("PRIMARY-SIDE TEST POINTS ARE LIVE - USE AN ISOLATED PROBE", 48, 94.6, 0.9, "C"),
]
# Enclosure (concept): board-local mm, z measured from the PCB top surface
ENC = dict(gap=1.5, wall=2.5, floor=2.5, standoff=6.0, pcb=1.6, inner_h=38.0, lid=2.5,
           openings=[("left", 4.0, 24.0, 15.0), ("right", 4.0, 24.0, 15.0), ("left", 80.0, 92.0, 11.0)])   # (wall, y0, y1, height)
