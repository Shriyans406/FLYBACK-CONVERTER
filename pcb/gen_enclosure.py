"""Generate a simple enclosure for the board from design.ENC:
  enclosure/ACF_enclosure_base.wrl, _lid.wrl  - 3D models shown in KiCad's 3D viewer
  enclosure/ACF_enclosure_base.stl, _lid.stl  - the same shapes in millimetres for CAD / 3D printing
The shapes are built from overlapping rectangular blocks: tray floor, four walls with wire
openings, four stand-off posts under the mounting holes, and a flat lid."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "enclosure")
os.makedirs(OUT, exist_ok=True)
E = D.ENC
W, H = D.BOARD_W, D.BOARD_H
xi0, xi1 = -E["gap"], W + E["gap"]                 # inner wall faces
yi0, yi1 = -E["gap"], H + E["gap"]
xo0, xo1 = xi0 - E["wall"], xi1 + E["wall"]        # outer wall faces
yo0, yo1 = yi0 - E["wall"], yi1 + E["wall"]
z_floor_top = -E["pcb"] - E["standoff"]
z_bottom = z_floor_top - E["floor"]
z_top = E["inner_h"]

base = [(xo0, yo0, z_bottom, xo1, yo1, z_floor_top)]                                             # floor
base += [(xo0, yo0, z_floor_top, xo1, yi0, z_top), (xo0, yi1, z_floor_top, xo1, yo1, z_top)]     # front / back walls


def side_wall(x0, x1, name):
    ops = sorted((y0, y1, h) for w, y0, y1, h in E["openings"] if w == name)
    y = yi0
    for y0, y1, h in ops:
        base.append((x0, y, z_floor_top, x1, y0, z_top))      # solid part before the opening
        base.append((x0, y0, z_floor_top, x1, y1, 0.0))       # sill below the opening (up to the PCB top)
        base.append((x0, y0, h, x1, y1, z_top))               # lintel above the opening
        y = y1
    base.append((x0, y, z_floor_top, x1, yi1, z_top))


side_wall(xo0, xi0, "left")
side_wall(xi1, xo1, "right")
for hx, hy in D.HOLES:                                        # stand-off posts under the PCB
    base.append((hx - 4, hy - 4, z_floor_top, hx + 4, hy + 4, -E["pcb"]))
lid = [(xo0, yo0, z_top, xo1, yo1, z_top + E["lid"])]

FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def corners(b):
    x0, y0, z0, x1, y1, z1 = b
    # KiCad model axes: X right, Y up (= minus board y), Z up
    return [(x0, -y1, z0), (x1, -y1, z0), (x1, -y0, z0), (x0, -y0, z0),
            (x0, -y1, z1), (x1, -y1, z1), (x1, -y0, z1), (x0, -y0, z1)]


def write_wrl(name, boxes, rgb, transp):
    with open(os.path.join(OUT, name), "w") as f:
        f.write("#VRML V2.0 utf8\n# units: 0.1 inch (KiCad VRML convention)\n")
        for b in boxes:
            pts = ", ".join("%.4f %.4f %.4f" % (x / 2.54, y / 2.54, z / 2.54) for x, y, z in corners(b))
            idx = ", ".join("%d,%d,%d,%d,-1" % q for q in FACES)
            f.write("Shape {\n  appearance Appearance { material Material { diffuseColor %g %g %g specularColor 0.2 0.2 0.2 "
                    "shininess 0.3 transparency %g } }\n" % (rgb[0], rgb[1], rgb[2], transp))
            f.write("  geometry IndexedFaceSet { solid TRUE ccw TRUE coord Coordinate { point [ %s ] } coordIndex [ %s ] }\n}\n" % (pts, idx))


def write_stl(name, boxes):
    with open(os.path.join(OUT, name), "w") as f:
        f.write("solid %s\n" % name)
        for b in boxes:
            c = corners(b)
            for q in FACES:
                for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                    f.write(" facet normal 0 0 0\n  outer loop\n")
                    for i in tri:
                        f.write("   vertex %.3f %.3f %.3f\n" % c[i])
                    f.write("  endloop\n endfacet\n")
        f.write("endsolid %s\n" % name)


write_wrl("ACF_enclosure_base.wrl", base, (0.25, 0.27, 0.30), 0.0)
write_wrl("ACF_enclosure_lid.wrl", lid, (0.6, 0.75, 0.9), 0.6)
write_stl("ACF_enclosure_base.stl", base)
write_stl("ACF_enclosure_lid.stl", lid)
print("enclosure: outer %.0f x %.0f x %.1f mm, %d base blocks" % (xo1 - xo0, yo1 - yo0, z_top + E["lid"] - z_bottom, len(base)))
