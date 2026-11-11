"""Stage 2 (run with normal python + numpy): clearance-aware 2-layer grid router.
Reads pads.json, writes routes.json (tracks + vias). Spacing rules come from design.clearance()."""
import json, os, sys, heapq, math, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
G = 0.1
W = int(round(D.BOARD_W / G)) + 1
H = int(round(D.BOARD_H / G)) + 1
S = W * H
EDGE = 0.6
PAD_LOCAL = {}

pads = json.load(open(os.path.join(HERE, "pads.json")))
objs = []            # dict(net, layers, rect, local)
for p in pads:
    local = PAD_LOCAL.get(D.NET_DOMAIN.get(p["net"]), 0.0) if (p["tht"] and p["net"]) else 0.0
    objs.append(dict(net=p["net"], layers=(0, 1) if p["tht"] else (0,), rect=(p["x0"], p["y0"], p["x1"], p["y1"]), local=local, pad=p))
for net, layer, r, hard in D.POURS:
    if hard:
        objs.append(dict(net=net, layers=(layer,), rect=r, local=0.0, pour=True))
for net, cx, cy in D.THERMAL_VIAS:
    for dx in (-2.5, 0, 2.5):
        for dy in (-2.5, 0, 2.5):
            objs.append(dict(net=net, layers=(0, 1), rect=(cx + dx - 0.3, cy + dy - 0.3, cx + dx + 0.3, cy + dy + 0.3), local=0.0))


def clr(a, b):
    if a is None or b is None:
        return 0.2
    return D.clearance(a, b)


def paint(arr, r, infl):
    x0 = max(0, int(math.ceil((r[0] - infl) / G - 1e-9))); x1 = min(W - 1, int(math.floor((r[2] + infl) / G + 1e-9)))
    y0 = max(0, int(math.ceil((r[1] - infl) / G - 1e-9))); y1 = min(H - 1, int(math.floor((r[3] + infl) / G + 1e-9)))
    if x1 >= x0 and y1 >= y0:
        arr[y0:y1 + 1, x0:x1 + 1] = True


def keepout(arr, half):
    m = EDGE + half
    n = int(math.ceil(m / G))
    arr[:n, :] = True; arr[-n:, :] = True; arr[:, :n] = True; arr[:, -n:] = True
    paint(arr, (D.BARRIER_X0, 0, D.BARRIER_X1, D.BOARD_H), half)
    for hx, hy in D.HOLES:
        paint(arr, (hx - 1.6, hy - 1.6, hx + 1.6, hy + 1.6), 0.5 + half)


def blocked_maps(net, w):
    blk = np.zeros((2, H, W), bool)
    vb = np.zeros((H, W), bool)
    for l in (0, 1):
        keepout(blk[l], w / 2)
    keepout(vb, D.VIA_D / 2)
    for o in objs:
        if o["net"] == net:
            continue
        c = max(clr(net, o["net"]), o["local"]) + 0.02
        for l in o["layers"]:
            paint(blk[l], o["rect"], c + w / 2)
        paint(vb, o["rect"], c + D.VIA_D / 2)
    return blk, vb


def rect_cells(r, shrink=0.1):
    x0 = int(math.ceil((r[0] + shrink) / G)); x1 = int(math.floor((r[2] - shrink) / G))
    y0 = int(math.ceil((r[1] + shrink) / G)); y1 = int(math.floor((r[3] - shrink) / G))
    if x1 < x0:
        x0 = x1 = int(round((r[0] + r[2]) / 2 / G))
    if y1 < y0:
        y0 = y1 = int(round((r[1] + r[3]) / 2 / G))
    return x0, y0, x1, y1


def pad_cells(o):
    r = o["rect"]
    return rect_cells(r, 0.2 * min(r[2] - r[0], r[3] - r[1]) if (o["pad"]["tht"] or o["pad"]["ref"].startswith("TP")) else 0.1)


def dist_rect(px, py, r):
    dx = max(r[0] - px, 0, px - r[2]); dy = max(r[1] - py, 0, py - r[3])
    return dx + dy


tracks, vias, failures = [], [], []


def astar(src_cells, tgt, blk, vb, layers_ok, anchor, bottom_cost, via_cost):
    blk0 = blk[0].tobytes(); blk1 = blk[1].tobytes(); vbb = vb.tobytes()
    t0 = tgt[0].tobytes(); t1 = tgt[1].tobytes()
    blkb = (blk0, blk1); tb = (t0, t1)
    ax0, ay0, ax1, ay1 = [v / G for v in anchor]

    def h(x, y):
        return 11 * (max(ax0 - x, 0, x - ax1) + max(ay0 - y, 0, y - ay1))
    heap = []; best = {}; came = {}
    for (l, x, y) in src_cells:
        k = ((l * S + y * W + x) << 3) | 4
        best[k] = 0; heapq.heappush(heap, (h(x, y), 0, k))
    moves = ((1, 0, 0), (-1, 0, 1), (0, 1, 2), (0, -1, 3))
    n = 0
    while heap:
        f, g, k = heapq.heappop(heap)
        if best.get(k, 1e18) < g:
            continue
        idx = k >> 3; d = k & 7
        l = idx // S; rem = idx - l * S; y = rem // W; x = rem - y * W
        if tb[l][rem]:
            path = [(l, x, y)]
            while k in came:
                k = came[k]; idx = k >> 3; l2 = idx // S; rem2 = idx - l2 * S
                path.append((l2, rem2 % W, rem2 // W))
            return path[::-1]
        n += 1
        if n > 4000000:
            return None
        step = 10 if l == 0 else bottom_cost
        for dx, dy, nd in moves:
            nx = x + dx; ny = y + dy
            if nx < 0 or ny < 0 or nx >= W or ny >= H:
                continue
            r2 = ny * W + nx
            if blkb[l][r2] and not tb[l][r2]:
                continue
            ng = g + step + (0 if (d == nd or d == 4) else 15)
            nk = ((l * S + r2) << 3) | nd
            if ng < best.get(nk, 1e18):
                best[nk] = ng; came[nk] = k
                heapq.heappush(heap, (ng + h(nx, ny), ng, nk))
        ol = 1 - l
        if ol in layers_ok and not vbb[rem] and not blkb[ol][rem]:
            ng = g + via_cost
            nk = ((ol * S + rem) << 3) | 4
            if ng < best.get(nk, 1e18):
                best[nk] = ng; came[nk] = k
                heapq.heappush(heap, (ng + h(x, y), ng, nk))
    return None


def route_net(net):
    w = D.TRACK_W.get(net, D.DEFAULT_W)
    dom = D.NET_DOMAIN[net]
    layers_ok = (0,) if dom in D.TOP_ONLY_DOMAINS else (0, 1)
    ground = net in ("PGND", "AGND", "SGND")
    npads = [o for o in objs if o.get("pad") and o["net"] == net]
    pours = [(l, r) for n, l, r, hard in D.POURS if n == net]
    if len(npads) + (1 if pours else 0) < 2:
        return
    w_full = w
    maps = {}
    def get_maps(width):
        if width not in maps:
            maps[width] = blocked_maps(net, width)
        return maps[width]
    blk, vb = get_maps(w)
    tgt = np.zeros((2, H, W), bool)
    anchors = []
    for l, r in pours:
        x0, y0, x1, y1 = rect_cells(r, 0.5)
        tgt[l, y0:y1 + 1, x0:x1 + 1] = True
        anchors.append(r)
    for o in npads:
        if o["pad"]["tht"] and pours:
            ring = np.zeros((H, W), bool)
            paint(ring, o["rect"], 0.9)
            for l in (0, 1):
                tgt[l] &= ~ring
    remaining = []
    for o in npads:
        cx = (o["rect"][0] + o["rect"][2]) / 2; cy = (o["rect"][1] + o["rect"][3]) / 2
        inpour = any(l in o["layers"] and r[0] <= cx <= r[2] and r[1] <= cy <= r[3] for l, r in pours)
        if inpour:
            x0, y0, x1, y1 = pad_cells(o)
            for l in o["layers"]:
                tgt[l, y0:y1 + 1, x0:x1 + 1] = True
            anchors.append(o["rect"])
        else:
            remaining.append(o)
    if not anchors:
        remaining.sort(key=lambda o: o["pad"]["ref"] in D.NARROW_REFS)
        o = remaining.pop(0)
        x0, y0, x1, y1 = pad_cells(o)
        for l in o["layers"]:
            tgt[l, y0:y1 + 1, x0:x1 + 1] = True
        anchors.append(o["rect"])
    while remaining:
        def key(o):
            cx = (o["rect"][0] + o["rect"][2]) / 2; cy = (o["rect"][1] + o["rect"][3]) / 2
            return min(dist_rect(cx, cy, a) for a in anchors)
        remaining.sort(key=key)
        o = remaining.pop(0)
        cx = (o["rect"][0] + o["rect"][2]) / 2; cy = (o["rect"][1] + o["rect"][3]) / 2
        anchor = min(anchors, key=lambda a: dist_rect(cx, cy, a))
        w = min(w_full, D.NARROW_REFS.get(o["pad"]["ref"], w_full))
        blk, vb = get_maps(w)
        x0, y0, x1, y1 = pad_cells(o)
        src = [(l, x, y) for l in o["layers"] if l in layers_ok or o["pad"]["tht"]
               for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) if not blk[l, y, x]]
        if not src:
            src = [(o["layers"][0], int(round(cx / G)), int(round(cy / G)))]
        path = astar(src, tgt & ~blk, blk, vb, layers_ok, anchor, 14 if ground else 24, 80 if ground else 300)
        p = o["pad"]
        if path is None:
            failures.append(f"{net}: {p['ref']}.{p['num']}")
            print("   FAILED", net, p["ref"], p["num"])
            continue
        # compress to segments / vias
        i = 0
        while i < len(path) - 1:
            l, x, y = path[i]
            l2, x2, y2 = path[i + 1]
            if l2 != l:
                vias.append((net, x * G, y * G))
                objs.append(dict(net=net, layers=(0, 1), rect=(x * G - D.VIA_D / 2, y * G - D.VIA_D / 2, x * G + D.VIA_D / 2, y * G + D.VIA_D / 2), local=0.0))
                tgt[:, y, x] = True
                i += 1
                continue
            j = i + 1
            dx, dy = x2 - x, y2 - y
            while j + 1 < len(path) and path[j + 1][0] == l and (path[j + 1][1] - path[j][1], path[j + 1][2] - path[j][2]) == (dx, dy):
                j += 1
            ex, ey = path[j][1], path[j][2]
            tracks.append((net, l, x * G, y * G, ex * G, ey * G, w))
            objs.append(dict(net=net, layers=(l,), rect=(min(x, ex) * G - w / 2, min(y, ey) * G - w / 2, max(x, ex) * G + w / 2, max(y, ey) * G + w / 2), local=0.0))
            tgt[l, min(y, ey):max(y, ey) + 1, min(x, ex):max(x, ex) + 1] = True
            anchors.append((min(x, ex) * G, min(y, ey) * G, max(x, ex) * G, max(y, ey) * G))
            i = j
        for l in o["layers"]:
            tgt[l, y0:y1 + 1, x0:x1 + 1] = True
        anchors.append(o["rect"])


t_start = time.time()
for net in D.NET_ORDER:
    t = time.time()
    route_net(net)
    print(f"{net:6s} done in {time.time() - t:5.1f}s  tracks={len(tracks)} vias={len(vias)}", flush=True)
missing = set(D.NET_DOMAIN) - set(D.NET_ORDER)
print("nets not in NET_ORDER:", missing)
json.dump(dict(tracks=tracks, vias=vias, failures=failures), open(os.path.join(HERE, "routes.json"), "w"))
print("total", round(time.time() - t_start, 1), "s; failures:", failures)
