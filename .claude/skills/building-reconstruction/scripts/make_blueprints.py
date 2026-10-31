#!/usr/bin/env python3
"""Validate building.json and generate SVG blueprint sheets.

Usage: make_blueprints.py projects/<slug> [--check]

Writes 05_blueprints/plan_<floor>.svg (one per floor) and
05_blueprints/elevation_<facade>.svg (one per facade; walls share a facade via
wall["facade"], default = wall id). A3 landscape, millimetres, standard scale.
"""
import argparse
import datetime
import json
import math
import sys
from html import escape
from pathlib import Path

GRADE = {"A": ("#2e7d32", "#c8e6c9"), "B": ("#1565c0", "#bbdefb"),
         "C": ("#ef6c00", "#ffe0b2"), "D": ("#c62828", "#ffcdd2")}
PAGE_W, PAGE_H = 420, 297
DRAW = (15, 15, 300, 260)  # x, y, w, h of drawing area in mm
SCALES = [20, 50, 100, 200, 500, 1000, 2000]


# ---------- model helpers ----------

def load(project):
    return json.loads((Path(project) / "04_model/building.json").read_text(encoding="utf-8"))


def wall_len(w):
    return math.dist(w["from"], w["to"])


def wall_z(model, w):
    f = next((f for f in model["floors"] if f["id"] == w.get("floor")), None)
    z0 = w.get("z0", f["z"] if f else 0.0)
    z1 = w.get("z1", (f["z"] + f["height"]) if f else z0 + 3.0)
    return z0, z1


def check(model):
    errs = []
    ids = {}
    for kind in ["floors", "walls", "openings", "ornaments", "sources"]:
        for el in model.get(kind) or []:
            if el["id"] in ids:
                errs.append(f"duplicate id {el['id']} ({kind} and {ids[el['id']]})")
            ids[el["id"]] = kind
    src = {s["id"] for s in model.get("sources") or []}
    floors = {f["id"] for f in model.get("floors") or []}
    walls = {w["id"]: w for w in model.get("walls") or []}
    graded = (model.get("walls") or []) + (model.get("openings") or []) + (model.get("ornaments") or [])
    if model.get("roof"):
        graded.append(dict(model["roof"], id="roof"))
    for el in graded:
        if el.get("confidence") not in GRADE:
            errs.append(f"{el['id']}: confidence must be A–D, got {el.get('confidence')!r}")
        for s in el.get("sources", []):
            if s not in src:
                errs.append(f"{el['id']}: unknown source {s}")
        if not el.get("sources") and el.get("confidence") in ("A", "B"):
            errs.append(f"{el['id']}: grade {el['confidence']} needs at least one source")
    for w in walls.values():
        if w.get("floor") not in floors:
            errs.append(f"{w['id']}: unknown floor {w.get('floor')}")
        if wall_len(w) <= 0:
            errs.append(f"{w['id']}: zero length")
    for o in model.get("openings") or []:
        w = walls.get(o.get("wall"))
        if not w:
            errs.append(f"{o['id']}: unknown wall {o.get('wall')}")
            continue
        z0, z1 = wall_z(model, w)
        if o["offset"] < 0 or o["offset"] + o["width"] > wall_len(w) + 1e-6:
            errs.append(f"{o['id']}: does not fit along {w['id']} (length {wall_len(w):.2f})")
        if o["sill"] < 0 or o["sill"] + o["height"] > (z1 - z0) + 1e-6:
            errs.append(f"{o['id']}: taller than {w['id']} ({z1 - z0:.2f} m)")
    for r in model.get("ornaments") or []:
        if r.get("wall") and r["wall"] not in walls:
            errs.append(f"{r['id']}: unknown wall {r['wall']}")
    roof = model.get("roof")
    if roof and roof.get("type") in ("gable", "hip") and len(roof.get("footprint", [])) != 4:
        errs.append("roof: gable/hip needs a 4-point rectangular footprint")
    return errs


# ---------- svg helpers ----------

class Sheet:
    def __init__(self):
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def line(self, a, b, stroke="#000", w=0.25, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                 f'stroke="{stroke}" stroke-width="{w}"{d}/>')

    def poly(self, pts, fill="none", stroke="#000", w=0.25, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"{d}/>')

    def text(self, p, s, size=2.5, anchor="middle", rot=0, weight="normal", fill="#000"):
        t = f' transform="rotate({rot:.1f} {p[0]:.2f} {p[1]:.2f})"' if rot else ""
        self.add(f'<text x="{p[0]:.2f}" y="{p[1]:.2f}" font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" fill="{fill}"{t}>{escape(str(s))}</text>')

    def svg(self):
        body = "\n".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" '
                f'viewBox="0 0 {PAGE_W} {PAGE_H}" font-family="Helvetica, Arial, sans-serif">\n'
                f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="#fff"/>\n{body}\n</svg>\n')


def pick_scale(w_m, h_m, avail_w, avail_h):
    for s in SCALES:
        if w_m * 1000 / s <= avail_w and h_m * 1000 / s <= avail_h:
            return s
    return SCALES[-1]


def frame_and_title(sh, model, title, scale):
    m = model["meta"]
    sh.poly([(5, 5), (PAGE_W - 5, 5), (PAGE_W - 5, PAGE_H - 5), (5, PAGE_H - 5)], w=0.5)
    x0 = 320
    sh.poly([(x0, 5), (PAGE_W - 5, 5), (PAGE_W - 5, PAGE_H - 5), (x0, PAGE_H - 5)], w=0.5)
    y = 16
    sh.text((x0 + 5, y), m.get("name") or "Unnamed building", 4.2, "start", weight="bold"); y += 7
    for s in [m.get("address", ""), f"{m.get('postal', '')} {m.get('country', '')}".strip(),
              f"State: {m.get('state') or '—'}", f"Built: {m.get('built') or '—'}",
              f"Architect: {m.get('architect') or 'unknown'}"]:
        sh.text((x0 + 5, y), s, 2.8, "start"); y += 5
    y += 4
    sh.line((x0, y), (PAGE_W - 5, y), w=0.35); y += 8
    sh.text((x0 + 5, y), title, 3.6, "start", weight="bold"); y += 6
    sh.text((x0 + 5, y), f"Scale 1:{scale} (A3)", 2.8, "start"); y += 5
    sh.text((x0 + 5, y), f"Generated {datetime.date.today().isoformat()}", 2.4, "start"); y += 9
    sh.text((x0 + 5, y), "Evidence grade (line colour)", 2.8, "start", weight="bold"); y += 5
    for g, label in [("A", "documented"), ("B", "measured"), ("C", "inferred"), ("D", "speculative")]:
        sh.poly([(x0 + 5, y - 2.5), (x0 + 11, y - 2.5), (x0 + 11, y), (x0 + 5, y)],
                fill=GRADE[g][1], stroke=GRADE[g][0], w=0.5)
        sh.text((x0 + 14, y), f"{g} — {label}", 2.6, "start"); y += 5
    sh.text((x0 + 5, PAGE_H - 22), "RECONSTRUCTION", 3.4, "start", weight="bold", fill="#c62828")
    sh.text((x0 + 5, PAGE_H - 17), "NOT A MEASURED SURVEY", 3.0, "start", weight="bold", fill="#c62828")
    disc = m.get("disclaimer", "")
    sh.text((x0 + 5, PAGE_H - 11), disc[:52], 2.0, "start")
    sh.text((x0 + 5, PAGE_H - 8), disc[52:104], 2.0, "start")


def scale_bar(sh, origin, k):
    x, y = origin
    for i in range(5):
        fill = "#000" if i % 2 == 0 else "#fff"
        sh.poly([(x + i * k, y), (x + (i + 1) * k, y), (x + (i + 1) * k, y + 1.5), (x + i * k, y + 1.5)],
                fill=fill, w=0.2)
        sh.text((x + i * k, y + 4.5), i, 2.2)
    sh.text((x + 5 * k, y + 4.5), "5 m", 2.2)


# ---------- plans ----------

def plan_sheet(model, floor):
    walls = [w for w in model["walls"] if w.get("floor") == floor["id"]]
    pts = [p for w in model["walls"] for p in (w["from"], w["to"])]
    minx, maxx = min(p[0] for p in pts) - 1, max(p[0] for p in pts) + 1
    miny, maxy = min(p[1] for p in pts) - 1, max(p[1] for p in pts) + 1
    scale = pick_scale(maxx - minx, maxy - miny, DRAW[2] - 30, DRAW[3] - 40)
    k = 1000 / scale
    ox = DRAW[0] + 20 + (DRAW[2] - 30 - (maxx - minx) * k) / 2
    oy = DRAW[1] + 15 + (DRAW[3] - 40 - (maxy - miny) * k) / 2
    P = lambda x, y: (ox + (x - minx) * k, oy + (maxy - y) * k)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    sh = Sheet()
    frame_and_title(sh, model, f"Plan — {floor['name']} (+{floor['z']:.2f})", scale)
    openings = {}
    for o in model.get("openings") or []:
        openings.setdefault(o["wall"], []).append(o)

    for w in walls:
        (ax, ay), (bx, by) = w["from"], w["to"]
        L = wall_len(w)
        dx, dy = (bx - ax) / L, (by - ay) / L
        nx, ny = -dy, dx
        t = w["thickness"] / 2
        col, fill = GRADE.get(w.get("confidence"), GRADE["D"])
        quad = lambda u0, u1, h: [P(ax + dx * u0 + nx * h, ay + dy * u0 + ny * h),
                                  P(ax + dx * u1 + nx * h, ay + dy * u1 + ny * h),
                                  P(ax + dx * u1 - nx * h, ay + dy * u1 - ny * h),
                                  P(ax + dx * u0 - nx * h, ay + dy * u0 - ny * h)]
        sh.poly(quad(-t, L + t, t), fill=fill, stroke=col, w=0.5)
        for o in openings.get(w["id"], []):
            u0, u1 = o["offset"], o["offset"] + o["width"]
            ocol = GRADE.get(o.get("confidence"), GRADE["D"])[0]
            if o["type"] == "niche":
                sh.poly(quad(u0, u1, t * 0.6), stroke=ocol, w=0.3, dash="1,0.8")
                continue
            sh.poly(quad(u0, u1, t + 0.02), fill="#fff", stroke="none", w=0)
            sh.line(P(ax + dx * u0 + nx * t, ay + dy * u0 + ny * t), P(ax + dx * u0 - nx * t, ay + dy * u0 - ny * t), ocol, 0.35)
            sh.line(P(ax + dx * u1 + nx * t, ay + dy * u1 + ny * t), P(ax + dx * u1 - nx * t, ay + dy * u1 - ny * t), ocol, 0.35)
            if o["type"] == "window":
                for h in (t / 3, 0, -t / 3):
                    sh.line(P(ax + dx * u0 + nx * h, ay + dy * u0 + ny * h),
                            P(ax + dx * u1 + nx * h, ay + dy * u1 + ny * h), ocol, 0.2)
            else:  # door / arch: leaf + swing toward the inside
                side = 1 if (cx - ax) * nx + (cy - ay) * ny > 0 else -1
                hx, hy = ax + dx * u0 + nx * t * side, ay + dy * u0 + ny * t * side
                ex, ey = hx + nx * o["width"] * side, hy + ny * o["width"] * side
                sh.line(P(hx, hy), P(ex, ey), ocol, 0.3)
                r = o["width"] * k
                end = P(hx + dx * o["width"], hy + dy * o["width"])
                sweep = 0 if side * 1 > 0 else 1
                s0 = P(ex, ey)
                sh.add(f'<path d="M {s0[0]:.2f} {s0[1]:.2f} A {r:.2f} {r:.2f} 0 0 {sweep} {end[0]:.2f} {end[1]:.2f}" '
                       f'fill="none" stroke="{ocol}" stroke-width="0.2" stroke-dasharray="1,0.6"/>')
            mid = P(ax + dx * (u0 + u1) / 2 - nx * (t + 0.6), ay + dy * (u0 + u1) / 2 - ny * (t + 0.6))
            sh.text(mid, o["id"], 1.6, fill=ocol)
        # wall length label, on the side away from the centroid
        mx, my = (ax + bx) / 2, (ay + by) / 2
        out = -1 if (cx - mx) * nx + (cy - my) * ny > 0 else 1
        lp = P(mx + nx * out * (t + 1.2), my + ny * out * (t + 1.2))
        ang = -math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        sh.text(lp, f"{w['id']}  {L:.2f}", 2.2, rot=ang, fill=col)

    for r in model.get("ornaments") or []:
        if not (floor["z"] <= r["position"][2] < floor["z"] + floor["height"]):
            continue
        x, y = r["position"][:2]
        hw, hd = r["size"][0] / 2, r["size"][1] / 2
        col = GRADE.get(r.get("confidence"), GRADE["D"])[0]
        sh.poly([P(x - hw, y - hd), P(x + hw, y - hd), P(x + hw, y + hd), P(x - hw, y + hd)], stroke=col, w=0.3, dash="0.8,0.5")
        sh.text(P(x, y - hd - 0.8), r["id"], 1.8, fill=col)

    # overall dimensions
    a, b = P(minx + 1, miny + 1), P(maxx - 1, miny + 1)
    yd = b[1] + 16
    sh.line((a[0], yd), (b[0], yd), w=0.25)
    for xx in (a[0], b[0]):
        sh.line((xx, yd - 1.5), (xx, yd + 1.5), w=0.25)
    sh.text(((a[0] + b[0]) / 2, yd - 1.2), f"{maxx - minx - 2:.2f}", 2.6)
    c, d = P(minx + 1, miny + 1), P(minx + 1, maxy - 1)
    xd = c[0] - 16
    sh.line((xd, c[1]), (xd, d[1]), w=0.25)
    for yy in (c[1], d[1]):
        sh.line((xd - 1.5, yy), (xd + 1.5, yy), w=0.25)
    sh.text((xd - 1.2, (c[1] + d[1]) / 2), f"{maxy - miny - 2:.2f}", 2.6, rot=-90)

    # north arrow and scale bar
    nx0, ny0 = DRAW[0] + 8, DRAW[1] + 10
    sh.poly([(nx0, ny0 - 6), (nx0 + 2.5, ny0 + 2), (nx0, ny0), (nx0 - 2.5, ny0 + 2)], fill="#000")
    sh.text((nx0, ny0 + 6), "N", 3, weight="bold")
    scale_bar(sh, (DRAW[0] + 5, PAGE_H - 20), k)
    return sh.svg()


# ---------- elevations ----------

def facades(model):
    groups = {}
    for w in model["walls"]:
        groups.setdefault(w.get("facade", w["id"]), []).append(w)
    return groups


def elevation_sheet(model, name, walls):
    base = walls[0]
    (ax, ay), (bx, by) = base["from"], base["to"]
    L = wall_len(base)
    dx, dy = (bx - ax) / L, (by - ay) / L
    pts = [p for w in model["walls"] for p in (w["from"], w["to"])]
    cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    mirror = (cx - ax) * dy - (cy - ay) * dx > 0  # centroid on the right → viewer on the left
    proj = lambda x, y: (x - ax) * dx + (y - ay) * dy
    spans = []
    for w in walls:
        u0, u1 = sorted((proj(*w["from"]), proj(*w["to"])))
        spans.append((w, u0, u1, *wall_z(model, w)))
    umin, umax = min(s[1] for s in spans), max(s[2] for s in spans)
    zmax = max(s[4] for s in spans)
    roof = model.get("roof")
    if roof:
        zmax = max(zmax, roof.get("ridge", zmax))
    U = lambda u: (umax - u) if mirror else (u - umin)
    scale = pick_scale(umax - umin + 4, zmax + 4, DRAW[2] - 30, DRAW[3] - 40)
    k = 1000 / scale
    ox = DRAW[0] + 20 + (DRAW[2] - 30 - (umax - umin) * k) / 2
    gy = DRAW[1] + DRAW[3] - 25
    P = lambda u, z: (ox + U(u) * k, gy - z * k)
    left, right = ox, ox + (umax - umin) * k

    sh = Sheet()
    frame_and_title(sh, model, f"Elevation — {name}", scale)
    sh.line((DRAW[0] + 5, gy), (DRAW[0] + DRAW[2] - 5, gy), w=0.6)
    sh.text((DRAW[0] + 6, gy + 4), "±0.00", 2.2, "start")
    opens = {}
    for o in model.get("openings") or []:
        opens.setdefault(o["wall"], []).append(o)
    for w, u0, u1, z0, z1 in spans:
        col, fill = GRADE.get(w.get("confidence"), GRADE["D"])
        sh.poly([P(u0, z0), P(u1, z0), P(u1, z1), P(u0, z1)], fill=fill, stroke=col, w=0.5)
        sh.text((left - 3, P(0, z1)[1] + 1), f"+{z1:.2f}", 2.2, "end")
        flip = proj(*w["from"]) > proj(*w["to"])
        for o in opens.get(w["id"], []):
            a = proj(*w["from"]) + (-1 if flip else 1) * o["offset"]
            b = a + (-1 if flip else 1) * o["width"]
            oa, ob = sorted((a, b))
            zs, ze = z0 + o["sill"], z0 + o["sill"] + o["height"]
            ocol = GRADE.get(o.get("confidence"), GRADE["D"])[0]
            dash = "1,0.8" if o["type"] == "niche" else None
            if o["type"] == "arch":
                r = (ob - oa) / 2
                p0, p1 = P(oa, zs), P(ob, zs)
                q0, q1 = P(oa, ze - r), P(ob, ze - r)
                rr = r * k
                sh.add(f'<path d="M {p0[0]:.2f} {p0[1]:.2f} L {q0[0]:.2f} {q0[1]:.2f} A {rr:.2f} {rr:.2f} 0 0 1 '
                       f'{q1[0]:.2f} {q1[1]:.2f} L {p1[0]:.2f} {p1[1]:.2f} Z" fill="#fff" stroke="{ocol}" stroke-width="0.35"/>')
            else:
                sh.poly([P(oa, zs), P(ob, zs), P(ob, ze), P(oa, ze)], fill="#fff", stroke=ocol, w=0.35, dash=dash)
                if o["type"] == "window":
                    m = (oa + ob) / 2
                    sh.line(P(m, zs), P(m, ze), ocol, 0.2)
                    sh.line(P(oa, zs + o["height"] * 0.7), P(ob, zs + o["height"] * 0.7), ocol, 0.2)
            sh.text(P((oa + ob) / 2, zs - 0.35), o["id"], 1.5, fill=ocol)
    ids = {w["id"] for w in walls}
    for r in model.get("ornaments") or []:
        if r.get("wall") not in ids:
            continue
        u = proj(*r["position"][:2])
        hw, z, h = r["size"][0] / 2, r["position"][2], r["size"][2]
        col = GRADE.get(r.get("confidence"), GRADE["D"])[0]
        sh.poly([P(u - hw, z), P(u + hw, z), P(u + hw, z + h), P(u - hw, z + h)], fill="none", stroke=col, w=0.4, dash="0.8,0.5")
        if r["type"] == "statue":  # simple silhouette marker
            c = P(u, z + h * 0.88)
            sh.add(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{h * 0.08 * k:.2f}" fill="none" stroke="{col}" stroke-width="0.3"/>')
        sh.text(P(u, z + h + 0.3), f"{r['id']} {r.get('name', '')}"[:40], 1.8, fill=col)
    if roof and roof.get("eaves") is not None:
        col = GRADE.get(roof.get("confidence"), GRADE["D"])[0]
        sh.line(P(umin, roof["eaves"]), P(umax, roof["eaves"]), col, 0.3, "2,1")
        sh.text((right + 2, P(0, roof["eaves"])[1] + 1), f"eaves +{roof['eaves']:.2f}", 2.0, "start", fill=col)
        if roof.get("ridge"):
            sh.line(P(umin, roof["ridge"]), P(umax, roof["ridge"]), col, 0.3, "0.6,1")
            sh.text((right + 2, P(0, roof["ridge"])[1] + 1), f"ridge +{roof['ridge']:.2f}", 2.0, "start", fill=col)
    a, b = P(umin, 0), P(umax, 0)
    yd = gy + 9
    sh.line((min(a[0], b[0]), yd), (max(a[0], b[0]), yd), w=0.25)
    sh.text(((a[0] + b[0]) / 2, yd - 1.2), f"{umax - umin:.2f}", 2.6)
    scale_bar(sh, (DRAW[0] + 5, PAGE_H - 20), k)
    return sh.svg()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--check", action="store_true", help="validate only")
    args = ap.parse_args()
    model = load(args.project)
    errs = check(model)
    for e in errs:
        print("ERROR:", e)
    if errs:
        sys.exit(1)
    print("building.json OK")
    if args.check:
        return
    out = Path(args.project) / "05_blueprints"
    out.mkdir(exist_ok=True)
    for f in model["floors"]:
        (out / f"plan_{f['id']}.svg").write_text(plan_sheet(model, f), encoding="utf-8")
        print("wrote", out / f"plan_{f['id']}.svg")
    for name, walls in facades(model).items():
        fn = out / f"elevation_{name}.svg"
        fn.write_text(elevation_sheet(model, walls[0].get("facade_name", name), walls), encoding="utf-8")
        print("wrote", fn)


if __name__ == "__main__":
    main()
