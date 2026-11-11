# Active-Clamp Flyback Converter (400 V → 54 V / 1 A)

Everything for this project lives in this one folder. There is one copy of each file.

## 1. What is where

| Path | What it is |
|---|---|
| `11-07-26.asc` | **The final LTspice design** (active-clamp flyback, closed loop) |
| `11-07-26.plt` | Plot layout LTspice loads automatically for that file |
| `11-07-26_RCD_original.asc` | Your original RCD-snubber version, kept as the only backup of it |
| `ACF_verification.png` | Waveform plots from the verified simulation |
| other `.asc` / `Draft*` files | Your earlier internship iterations (untouched) |
| `pcb/ACF_Flyback.kicad_pro` | **KiCad project — open this one** |
| `pcb/ACF_Flyback.kicad_sch` | Schematic |
| `pcb/ACF_Flyback.kicad_pcb` | Routed 2-layer board |
| `pcb/ACF_Flyback.kicad_dru` | High-voltage spacing rules used by the design-rule check |
| `pcb/ACF.kicad_sym`, `pcb/sym-lib-table` | Schematic symbols used by this project |
| `pcb/design.py` | **The single source of truth**: parts, values, positions, nets, spacing rules, copper pours |
| `pcb/gen_schematic.py`, `build_1_place.py`, `route.py`, `build_3_finish.py`, `make_bom.py` | Scripts that turn `design.py` into the schematic, board and BOM |
| `pcb/build_all.bat` | Runs all of the above in order |
| `pcb/check_netlist.py` | Cross-checks the schematic netlist against `design.py` |
| `pcb/pads.json`, `pcb/routes.json` | Intermediate data passed between the build scripts |
| `pcb/fab/gerbers/` | Gerber + drill files for the PCB manufacturer |
| `pcb/fab/ACF_Flyback_BOM.csv` | Bill of materials |
| `pcb/fab/ACF_Flyback_CPL.csv` | Pick-and-place (component position) file |
| `pcb/fab/ACF_Flyback_schematic.pdf` | Schematic as a PDF |
| `pcb/fab/DRC_report.txt`, `ERC_report.txt` | Board and schematic check reports |
| `pcb/renders/top.png`, `bottom.png` | 3D renders of the board |

### Usability features on the board (converter values unchanged)

| Feature | Where | What it is for |
|---|---|---|
| **HV LIVE** red LED (`D3`, `R26`–`R28`) | primary, left of centre | Lit while the bulk capacitor is charged. Do not touch the board until it goes out. Draws about 0.6 mA from the 400 V rail. |
| **BIAS** yellow LED (`D4`, `R25`) | next to the 12 V header | Shows the controller supply is present. |
| **OUTPUT ON** green LED (`D5`, `R24`) | secondary, lower right | Shows 54 V is present. Draws about 2 mA. |
| Probe loops `TP1` VOUT, `TP2` RTN | secondary, lower right | Clip a multimeter or scope here to measure the output safely. |
| Probe points `TP3` VCC, `TP4` PGND, `TP5` CS, `TP6` GATE | primary | Debug points. **These are on the live side: use an isolated or differential probe.** |
| Silkscreen legends | at every connector, LED and test point | Polarity (`+400V`/`GND`, `+54V`/`RTN`), fuse rating, bias pin order, and a discharge warning. |
| Rounded corners (3 mm) | board outline | Safer handling, easier fit in a case. |
| Fiducials `FID1`–`FID3` | three corners | Alignment marks for machine assembly. |
| Enclosure | `pcb/enclosure/` | 163 × 108 × 51 mm tray with stand-offs under the four M3 holes, wire openings at both terminal blocks and the bias header, and a flat lid. |

Enclosure files: `ACF_enclosure_base.wrl` / `_lid.wrl` are what KiCad's 3D viewer shows; `ACF_enclosure_base.stl` / `_lid.stl` are the same shapes in millimetres for CAD or 3D printing. `gen_enclosure.py` creates them from the `ENC` settings in `design.py`.

To see the enclosure in KiCad: open the board, press **Alt+3**. The base is shown; the lid is hidden so it does not cover the board. To show the lid, double-click footprint `ENC2` (select it via **Edit → Find**, search `ENC2`), go to the **3D Models** tab and tick **Show**. To hide the whole case, untick **Show** on `ENC1` the same way. The case outline is also drawn on the `User.Drawings` layer.

## 2. How to view everything

### LTspice simulation
1. Double-click `11-07-26.asc` (opens in LTspice).
2. Press the **Run** button (running man). The run takes about 2 minutes.
3. Four plots appear automatically: `V(out)`, `V(ds)`, `I(L1)`, and duty/soft-start.
4. Click any wire to plot its voltage; click a component to plot its current.
5. **View → SPICE Output Log** (Ctrl+L) shows the measured numbers: output voltage, ripple, efficiency, duty, peak `V(ds)`, and `V(ds)` at turn-on (the zero-voltage-switching check).
6. To see zero-voltage switching: zoom into the last few cycles and plot `V(ds)` together with `V(gs)`.

The `.raw` result file is about 430 MB, so it was deleted to save space. LTspice recreates it each time you press Run.

### KiCad schematic and board
1. Open **KiCad**, then **File → Open Project** and pick `pcb/ACF_Flyback.kicad_pro`.
2. Double-click the schematic file to open the **Schematic Editor**. The sheet is split into six numbered sections. Every pin carries a net label instead of drawn wires; pins with the same label are connected. Click a label and press **`** (backtick) to highlight that net.
3. Double-click the board file to open the **PCB Editor**.
   - **View → 3D Viewer** (Alt+3) shows the board in 3D.
   - Use the layer list on the right to show only `F.Cu` (top copper) or `B.Cu` (bottom copper).
   - Click any pad or track and press **`** to highlight its whole net.
   - **Inspect → Design Rules Checker → Run DRC** re-runs the check. Tick "Test for parity between PCB and schematic" to compare against the schematic.
4. Manufacturing files: in the KiCad project window choose **Gerber Viewer**, then **File → Open Gerber Job File** and pick `pcb/fab/gerbers/ACF_Flyback-job.gbrjob`. Then **File → Open Excellon Drill File** and pick `ACF_Flyback.drl`.
5. `BOM.csv` and `CPL.csv` open in Excel. The PDF and PNG files open with any viewer.

## 3. How to change things

### LTspice
- Right-click a component to change its value; right-click a blue text line to edit a directive.
- Useful knobs: `C1` (output capacitor), `L1`/`L2` (transformer, keep the 100:1 inductance ratio for 10:1 turns), `Cclamp`, `R2`/`C2`/`C3` (compensator), `Vss` (soft-start ramp), `Istep` (load step; delete it for a plain steady-state run).
- `.options reltol=0.001` gives clean waveforms. Changing it to `0.01` runs about 3× faster but adds a fake low-frequency wobble.

### PCB — two ways, do not mix them
**A. Edit by hand in KiCad** (best for small moves or re-routing):
edit the schematic or board in KiCad and save. Then use **Tools → Update PCB from Schematic** as normal.
Do **not** run `build_all.bat` afterwards — it regenerates the files and overwrites hand edits.

**B. Edit `pcb/design.py` and regenerate** (best for changing parts, values, positions or spacing rules):
1. Close KiCad (it locks the files).
2. Open `pcb/design.py` in any text editor.
   - `PARTS` — one line per component: footprint, value, x/y position in mm, rotation, and which pad goes to which net.
   - `clearance()` — the spacing rules between voltage domains.
   - `POURS` — the copper pour rectangles.
   - `TRACK_W` — track widths per net.
3. Double-click `pcb/build_all.bat`. It takes about 2 minutes.
4. Read `pcb/fab/DRC_report.txt` and `pcb/fab/ERC_report.txt`, then open the project in KiCad to look.

If the router prints `FAILED` for a net, two parts are too close for the spacing rules: move one of them in `PARTS` and run again.

## 4. How it was built

### Simulation
1. Read the internship report and the original `11-07-26.asc` (RCD-snubber flyback).
2. Replaced the RCD snubber with an active clamp (clamp MOSFET `M2` + `Cclamp`), driven complementary to `M1` with 0.5 µs dead-time.
3. Raised the transformer inductance from 572 µH to 25 mH so the magnetising current swings negative each cycle. That is what gives zero-voltage switching and removes the idle period that caused ringing.
4. Replaced the generic MOSFET with a model of the Infineon IMBF170R1K0M1, fitted to its datasheet values.
5. Recalculated the output capacitor for the new operating point (180 µF) and retuned the compensator.
6. Added a duty soft-start and an anti-windup clamp on the error amplifier.
7. Ran LTspice in batch mode after each change and read the `.meas` results until output voltage, ripple, zero-voltage switching and a load step all checked out.

### PCB
1. Chose real parts for what LTspice modelled as ideal blocks: LM5025 controller, UCC5350 isolated high-side driver with bootstrap diode, TL431 + optocoupler feedback, fuse, bulk capacitor, Y capacitor.
2. Wrote the whole design as data in `design.py`.
3. `build_1_place.py` (KiCad's Python) creates the board outline and isolation slots and places every footprint from the KiCad libraries.
4. `route.py` is a grid router written for this board. It routes each net on a 0.1 mm grid and keeps the spacing each voltage domain needs.
5. `build_3_finish.py` adds the tracks, vias, thermal vias, copper pours and bottom-side high-voltage keep-outs, fills the zones, and writes the DRC rule file.
6. `gen_schematic.py` writes the schematic from the same data, so the schematic and board cannot disagree.
7. KiCad's own checks were then run from the command line: DRC with schematic parity, and ERC. Result: 0 errors, 0 unconnected nets, 0 parity issues, 14 silkscreen warnings.
8. Gerbers, drill, placement, BOM, PDF and renders were exported with `kicad-cli`.

## 5. Known limits — read before ordering boards

- **Transformer footprint is a placeholder** (library ETD29 bobbin). A 25 mH, 10 kHz transformer needs a larger core; replace the footprint once the transformer is designed.
- **10 kHz is unusually low for the LM5025**; check its oscillator range or raise the switching frequency.
- **MOSFET footprint is the generic TO-263-7 pattern**; check it against Infineon's package drawing.
- **Spacing values are engineering choices** (8 mm primary-to-secondary, 3 mm around 1 kV nets, 2.5 mm around 400 V), not checked against a specific safety standard. 3 mm at 1 kV assumes conformal coating.
- **The TL431/optocoupler loop values are starting points**; that loop was not simulated.
- **Pin assumptions to check on datasheets:** LM5025 VIN tied to VCC for 12 V operation; TL431 pin order for the vendor you buy.
- **The BOM has no manufacturer part numbers for passives**, and the placement file includes through-hole parts.
- **Controller bias is an external 12 V header**, not an auxiliary winding.
- **The enclosure is a concept model.** It is plain blocks: no screw holes in the stand-offs, no lid fixings, no vents, and its 38 mm inner height has not been checked against a real transformer. The STL files are overlapping solids and have not been test-printed. Choose a flame-rated insulating material for a 400 V product.
- **The two indicator LEDs on the power rails add small loads** (about 0.6 mA at 400 V and 2 mA at 54 V); these were not added to the LTspice model.
