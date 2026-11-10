@echo off
rem Rebuilds the whole KiCad project from design.py. Close KiCad first (it locks the files).
rem WARNING: this overwrites ACF_Flyback.kicad_pcb and .kicad_sch, including any edits made by hand in KiCad.
setlocal
cd /d "%~dp0"
set KPY="C:\Program Files\KiCad\10.0\bin\python.exe"
set KCLI="C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
if not exist fab\gerbers mkdir fab\gerbers
if not exist renders mkdir renders
python gen_schematic.py || goto :err
%KPY% build_1_place.py || goto :err
python route.py || goto :err
%KPY% build_3_finish.py || goto :err
%KCLI% pcb drc --severity-all --schematic-parity --refill-zones --save-board -o fab\DRC_report.txt ACF_Flyback.kicad_pcb
%KCLI% sch erc --severity-all -o fab\ERC_report.txt ACF_Flyback.kicad_sch
%KCLI% pcb export gerbers -o fab\gerbers\ --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts" ACF_Flyback.kicad_pcb
%KCLI% pcb export drill -o fab\gerbers\ --format excellon --excellon-units mm ACF_Flyback.kicad_pcb
%KCLI% pcb export pos --format csv --units mm --side both -o fab\ACF_Flyback_CPL.csv ACF_Flyback.kicad_pcb
%KCLI% sch export pdf -o fab\ACF_Flyback_schematic.pdf ACF_Flyback.kicad_sch
%KCLI% pcb render --side top -w 1600 -h 1100 -o renders\top.png ACF_Flyback.kicad_pcb
%KCLI% pcb render --side bottom -w 1600 -h 1100 -o renders\bottom.png ACF_Flyback.kicad_pcb
python make_bom.py
echo Done. Read fab\DRC_report.txt and fab\ERC_report.txt.
exit /b 0
:err
echo Build failed - see the message above.
exit /b 1
