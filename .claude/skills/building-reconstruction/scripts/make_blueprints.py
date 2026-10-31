#!/usr/bin/env python3
"""Validate building.json and generate SVG blueprint sheets.

Usage: make_blueprints.py projects/<slug> [--check] [--year 1900]

Writes to 05_blueprints/:
  plan_<floor>.svg       one per floor: walls, partitions, openings, rooms with areas, stairs
  plan_roof.svg          roof plan: every roof part, ridges and hips
  elevation_<facade>.svg one per facade (walls share a facade via wall["facade"])
A3 landscape, millimetres, standard scale. --year draws the state in that
year (elements carry "period": [from, to]); default is meta.year if set.
"""
import argparse
import datetime
import math
import sys
from html import escape
from pathlib import Path

from geometry import (at_year, building_centroid, check, load_model, poly_area, poly_centroid,
                      roof_faces, stair_steps, wall_len, wall_z)

GRADE = {"A": ("#2e7d32", "#c8e6c9"), "B": ("#1565c0", "#bbdefb"),
         "C": ("#ef6c00", "#ffe0b2"), "D": ("#c62828", "#ffcdd2")}
PAGE_W, PAGE_H = 420, 297
DRAW = (15, 15, 300, 260)  # x, y, w, h of drawing area in mm
SCALES = [20, 50, 100, 200, 500, 1000, 2000]


def gcol(el):
    return GRADE.get(el.get("confidence"), GRADE["D"])


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

    def poly(self, pts, fill="none", stroke="#000", w=0.25, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"{d}{o}/>')

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


def frame_and_title(sh, model, title, scale, year):
    m = model["meta"]
    sh.poly([(5, 5), (PAGE_W - 5, 5), (PAGE_W - 5, PAGE_H - 5), (5, PAGE_H - 5)], w=0.5)
    x0 = 320
    sh.poly([(x0, 5), (PAGE_W - 5, 5), (PAGE_W - 5, PAGE_H - 5), (x0, PAGE_H - 5)], w=0.5)
    y = 16
    name = m.get("name") or "Unnamed building"
    sh.text((x0 + 5, y), name[:34], 4.0, "start", weight="bold"); y += 5.5
    if len(name) > 34:
        sh.text((x0 + 5, y), name[34:68], 4.0, "start", weight="bold"); y += 5.5
    y += 1.5
    for s in [m.get("address", ""), f"{m.get('postal', '')} {m.get('district', '')}".strip(),
              f"Parcel (hrsz.): {m.get('hrsz') or '—'}",
              f"State shown: {year if year is not None else (m.get('state') or 'all periods')}",
              f"Built: {m.get('built') or '—'}", f"Architect: {m.get('architect') or 'unknown'}"]:
        sh.text((x0 + 5, y), s, 2.8, "start"); y += 5
    y += 3
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
    step = 1 if k >= 8 else 5 if k >= 1.5 else 10
    for i in range(5):
        fill = "#000" if i % 2 == 0 else "#fff"
        sh.poly([(x + i * k * step, y), (x + (i + 1) * k * step, y), (x + (i + 1) * k * step, y + 1.5),
                 (x + i * k * step, y + 1.5)], fill=fill, w=0.2)
        sh.text((x + i * k * step, y + 4.5), i * step, 2.2)
    sh.text((x + 5 * k * step, y + 4.5), f"{5 * step} m", 2.2)


def north_arrow(sh):
    nx0, ny0 = DRAW[0] + 8, DRAW[1] + 10
    sh.poly([(nx0, ny0 - 6), (nx0 + 2.5, ny0 + 2), (nx0, ny0), (nx0 - 2.5, ny0 + 2)], fill="#000")
    sh.text((nx0, ny0 + 6), "N", 3, weight="bold")


def plan_frame(model):
    pts = [p for w in model["walls"] for p in (w["from"], w["to"])]
    for r in model["roofs"]:
        pts += [f[:2] for face in roof_faces(r) for f in face]
    minx, maxx = min(p[0] for p in pts) - 1, max(p[0] for p in pts) + 1
    miny, maxy = min(p[1] for p in pts) - 1, max(p[1] for p in pts) + 1
    scale = pick_scale(maxx - minx, maxy - miny, DRAW[2] - 30, DRAW[3] - 40)
    k = 1000 / scale
    ox = DRAW[0] + 20 + (DRAW[2] - 30 - (maxx - minx) * k) / 2
    oy = DRAW[1] + 15 + (DRAW[3] - 40 - (maxy - miny) * k) / 2
    P = lambda x, y: (ox + (x - minx) * k, oy + (maxy - y) * k)
    return P, k, scale, (minx, maxx, miny, maxy)


# ---------- plans ----------

def plan_sheet(model, floor, year):
    walls = [w for w in model["walls"] if w.get("floor") == floor["id"]]
    P, k, scale, (minx, maxx, miny, maxy) = plan_frame(model)
    cx, cy = building_centroid(model)

    sh = Sheet()
    frame_and_title(sh, model, f"Plan — {floor['name']} (+{floor['z']:.2f})", scale, year)

    for r in model["rooms"]:
        if r["floor"] != floor["id"]:
            continue
        sh.poly([P(*p) for p in r["polygon"]], fill="#f5f5f5", stroke="none", w=0)
        c = P(*poly_centroid(r["polygon"]))
        sh.text(c, r.get("name", r["id"]), 2.4, weight="bold")
        sh.text((c[0], c[1] + 3.2), f"{r['id']} · {poly_area(r['polygon']):.1f} m²", 2.0)

    openings = {}
    for o in model["openings"]:
        openings.setdefault(o["wall"], []).append(o)

    for w in walls:
        (ax, ay), (bx, by) = w["from"], w["to"]
        L = wall_len(w)
        dx, dy = (bx - ax) / L, (by - ay) / L
        nx, ny = -dy, dx
        t = w["thickness"] / 2
        col, fill = gcol(w)
        if w.get("interior"):
            fill = "#ffffff"
        quad = lambda u0, u1, h: [P(ax + dx * u0 + nx * h, ay + dy * u0 + ny * h),
                                  P(ax + dx * u1 + nx * h, ay + dy * u1 + ny * h),
                                  P(ax + dx * u1 - nx * h, ay + dy * u1 - ny * h),
                                  P(ax + dx * u0 - nx * h, ay + dy * u0 - ny * h)]
        ext = 0 if w.get("interior") else t
        sh.poly(quad(-ext, L + ext, t), fill=fill, stroke=col, w=0.35 if w.get("interior") else 0.5)
        for o in openings.get(w["id"], []):
            u0, u1 = o["offset"], o["offset"] + o["width"]
            ocol = gcol(o)[0]
            if o["type"] == "niche":
                sh.poly(quad(u0, u1, t * 0.6), stroke=ocol, w=0.3, dash="1,0.8")
                continue
            sh.poly(quad(u0, u1, t + 0.02), fill="#fff", stroke="none", w=0)
            for u in (u0, u1):
                sh.line(P(ax + dx * u + nx * t, ay + dy * u + ny * t), P(ax + dx * u - nx * t, ay + dy * u - ny * t), ocol, 0.35)
            if o["type"] in ("window", "shopfront"):
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
                s0 = P(ex, ey)
                sweep = 0 if side > 0 else 1
                sh.add(f'<path d="M {s0[0]:.2f} {s0[1]:.2f} A {r:.2f} {r:.2f} 0 0 {sweep} {end[0]:.2f} {end[1]:.2f}" '
                       f'fill="none" stroke="{ocol}" stroke-width="0.2" stroke-dasharray="1,0.6"/>')
            mid = P(ax + dx * (u0 + u1) / 2 - nx * (t + 0.6), ay + dy * (u0 + u1) / 2 - ny * (t + 0.6))
            sh.text(mid, o["id"], 1.6, fill=ocol)
        if not w.get("interior"):
            mx, my = (ax + bx) / 2, (ay + by) / 2
            out = -1 if (cx - mx) * nx + (cy - my) * ny > 0 else 1
            lp = P(mx + nx * out * (t + 1.2), my + ny * out * (t + 1.2))
            ang = -math.degrees(math.atan2(dy, dx))
            if ang > 90 or ang < -90:
                ang += 180
            sh.text(lp, f"{w['id']}  {L:.2f}", 2.2, rot=ang, fill=col)

    for s in model["stairs"]:
        if s["floor"] != floor["id"]:
            continue
        col = gcol(s)[0]
        steps, lines = stair_steps(model, s)
        for st in steps:
            sh.poly([P(*p) for p in st["poly"]], fill="#fff", stroke=col, w=0.25)
        for a, b in lines:
            pa, pb = P(*a), P(*b)
            sh.line(pa, pb, col, 0.3)
            ang = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
            for da in (2.6, -2.6):
                sh.line(pb, (pb[0] - 2 * math.cos(ang + da / 6), pb[1] - 2 * math.sin(ang + da / 6)), col, 0.3)
        a0 = P(*lines[0][0])
        sh.text((a0[0], a0[1] + 3), f"{s['id']} UP {s['steps']}×", 1.8, fill=col)

    for r in model["ornaments"]:
        if not (floor["z"] <= r["position"][2] < floor["z"] + floor["height"]):
            continue
        x, y = r["position"][:2]
        hw, hd = r["size"][0] / 2, r["size"][1] / 2
        col = gcol(r)[0]
        sh.poly([P(x - hw, y - hd), P(x + hw, y - hd), P(x + hw, y + hd), P(x - hw, y + hd)], stroke=col, w=0.3, dash="0.8,0.5")
        sh.text(P(x, y - hd - 0.8), r["id"], 1.8, fill=col)

    ext = [p for w in model["walls"] if not w.get("interior") for p in (w["from"], w["to"])]
    ex0, ex1 = min(p[0] for p in ext), max(p[0] for p in ext)
    ey0, ey1 = min(p[1] for p in ext), max(p[1] for p in ext)
    a, b = P(ex0, ey0), P(ex1, ey0)
    yd = P(0, miny)[1] + 6
    sh.line((a[0], yd), (b[0], yd), w=0.25)
    for xx in (a[0], b[0]):
        sh.line((xx, yd - 1.5), (xx, yd + 1.5), w=0.25)
    sh.text(((a[0] + b[0]) / 2, yd - 1.2), f"{ex1 - ex0:.2f}", 2.6)
    c, d = P(ex0, ey0), P(ex0, ey1)
    xd = P(minx, 0)[0] - 6
    sh.line((xd, c[1]), (xd, d[1]), w=0.25)
    for yy in (c[1], d[1]):
        sh.line((xd - 1.5, yy), (xd + 1.5, yy), w=0.25)
    sh.text((xd - 1.2, (c[1] + d[1]) / 2), f"{ey1 - ey0:.2f}", 2.6, rot=-90)

    north_arrow(sh)
    scale_bar(sh, (DRAW[0] + 5, PAGE_H - 20), k)
    return sh.svg()


def roof_plan_sheet(model, year):
    P, k, scale, _ = plan_frame(model)
    sh = Sheet()
    frame_and_title(sh, model, "Roof plan", scale, year)
    for w in model["walls"]:
        if not w.get("interior"):
            sh.line(P(*w["from"]), P(*w["to"]), "#999", 0.25, "1,1")
    for r in model["roofs"]:
        col, fill = gcol(r)
        faces = roof_faces(r)
        for f in faces:
            sh.poly([P(p[0], p[1]) for p in f], fill=fill, stroke=col, w=0.3 if r["type"] != "dome" else 0.1)
        top = max(p[2] for f in faces for p in f)
        if r["type"] == "dome":  # label below the dome, clear of the roof it sits on
            rad = r["radius"] if not isinstance(r["radius"], list) else r["radius"][1]
            c = P(r["center"][0], r["center"][1] - rad - 1.0)
        elif r["type"] == "flat":
            c = P(*poly_centroid([p[:2] for p in faces[0]]))
        else:
            c = P(*[sum(p[i] for f in faces for p in f) / sum(len(f) for f in faces) for i in (0, 1)])
        sh.text(c, f"{r['id']} {r['type']}", 2.4, weight="bold", fill=col)
        sh.text((c[0], c[1] + 3.2), f"eaves +{r.get('eaves', 0):.2f} / top +{top:.2f}", 2.0, fill=col)
    north_arrow(sh)
    scale_bar(sh, (DRAW[0] + 5, PAGE_H - 20), k)
    return sh.svg()


# ---------- elevations ----------

def facades(model):
    groups = {}
    for w in model["walls"]:
        if not w.get("interior"):
            groups.setdefault(w.get("facade", w["id"]), []).append(w)
    return groups


def elevation_sheet(model, name, walls, year):
    base = walls[0]
    (ax, ay), (bx, by) = base["from"], base["to"]
    L = wall_len(base)
    dx, dy = (bx - ax) / L, (by - ay) / L
    cx, cy = building_centroid(model)
    inward = 1 if (cx - ax) * (-dy) + (cy - ay) * dx > 0 else -1  # +left normal points inside?
    nin = (-dy * inward, dx * inward)
    mirror = inward < 0  # building on the right of the wall direction → viewer on the left → flip
    proj = lambda x, y: (x - ax) * dx + (y - ay) * dy
    depth = lambda x, y: (x - ax) * nin[0] + (y - ay) * nin[1]
    spans = []
    for w in walls:
        u0, u1 = sorted((proj(*w["from"]), proj(*w["to"])))
        spans.append((w, u0, u1, *wall_z(model, w)))
    roof_polys = []
    for r in model["roofs"]:
        for f in roof_faces(r):
            roof_polys.append((sum(depth(p[0], p[1]) for p in f) / len(f), r, [(proj(p[0], p[1]), p[2]) for p in f]))
    us = [s[1] for s in spans] + [s[2] for s in spans] + [u for _, _, f in roof_polys for u, _ in f]
    umin, umax = min(us), max(us)
    zmax = max([s[4] for s in spans] + [z for _, _, f in roof_polys for _, z in f])
    U = lambda u: (umax - u) if mirror else (u - umin)
    scale = pick_scale(umax - umin + 4, zmax + 4, DRAW[2] - 30, DRAW[3] - 40)
    k = 1000 / scale
    ox = DRAW[0] + 20 + (DRAW[2] - 30 - (umax - umin) * k) / 2
    gy = DRAW[1] + DRAW[3] - 25
    P = lambda u, z: (ox + U(u) * k, gy - z * k)
    left, right = ox, ox + (umax - umin) * k

    sh = Sheet()
    frame_and_title(sh, model, f"Elevation — {name}", scale, year)
    sh.line((DRAW[0] + 5, gy), (DRAW[0] + DRAW[2] - 5, gy), w=0.6)
    sh.text((DRAW[0] + 6, gy + 4), "±0.00", 2.2, "start")
    for _, r, f in sorted(roof_polys, key=lambda t: -t[0]):  # far faces first
        col, fill = gcol(r)
        sh.poly([P(u, z) for u, z in f], fill=fill, stroke=col, w=0.08 if r["type"] == "dome" else 0.25)
    opens = {}
    for o in model["openings"]:
        opens.setdefault(o["wall"], []).append(o)
    for w, u0, u1, z0, z1 in sorted(spans, key=lambda s: -depth(*s[0]["from"])):
        col, fill = gcol(w)
        sh.poly([P(u0, z0), P(u1, z0), P(u1, z1), P(u0, z1)], fill=fill, stroke=col, w=0.5)
        sh.text((left - 3, P(0, z1)[1] + 1), f"+{z1:.2f}", 2.2, "end")
        flip = proj(*w["from"]) > proj(*w["to"])
        for o in opens.get(w["id"], []):
            a = proj(*w["from"]) + (-1 if flip else 1) * o["offset"]
            b = a + (-1 if flip else 1) * o["width"]
            oa, ob = sorted((a, b))
            zs, ze = z0 + o["sill"], z0 + o["sill"] + o["height"]
            ocol = gcol(o)[0]
            dash = "1,0.8" if o["type"] == "niche" else None
            if o["type"] == "arch":
                r = (ob - oa) / 2
                p0, p1 = P(oa, zs), P(ob, zs)
                q0, q1 = P(oa, ze - r), P(ob, ze - r)
                rr = r * k
                sweep = 0 if mirror else 1
                sh.add(f'<path d="M {p0[0]:.2f} {p0[1]:.2f} L {q0[0]:.2f} {q0[1]:.2f} A {rr:.2f} {rr:.2f} 0 0 {sweep} '
                       f'{q1[0]:.2f} {q1[1]:.2f} L {p1[0]:.2f} {p1[1]:.2f} Z" fill="#fff" stroke="{ocol}" stroke-width="0.35"/>')
            else:
                sh.poly([P(oa, zs), P(ob, zs), P(ob, ze), P(oa, ze)], fill="#fff", stroke=ocol, w=0.35, dash=dash)
                if o["type"] == "window":
                    m = (oa + ob) / 2
                    sh.line(P(m, zs), P(m, ze), ocol, 0.2)
                    sh.line(P(oa, zs + o["height"] * 0.7), P(ob, zs + o["height"] * 0.7), ocol, 0.2)
                elif o["type"] == "shopfront":
                    for i in range(1, 4):
                        uu = oa + (ob - oa) * i / 4
                        sh.line(P(uu, zs), P(uu, ze), ocol, 0.2)
            sh.text(P((oa + ob) / 2, zs - 0.35), o["id"], 1.5, fill=ocol)
    ids = {w["id"] for w in walls}
    for r in model["ornaments"]:
        if r.get("wall") not in ids:
            continue
        u = proj(*r["position"][:2])
        hw, z, h = r["size"][0] / 2, r["position"][2], r["size"][2]
        col = gcol(r)[0]
        sh.poly([P(u - hw, z), P(u + hw, z), P(u + hw, z + h), P(u - hw, z + h)], fill="none", stroke=col, w=0.4, dash="0.8,0.5")
        if r["type"] == "statue":
            c = P(u, z + h * 0.88)
            sh.add(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{h * 0.08 * k:.2f}" fill="none" stroke="{col}" stroke-width="0.3"/>')
        sh.text(P(u, z + h + 0.3), f"{r['id']} {r.get('name', '')}"[:40], 1.8, fill=col)
    if model["roofs"]:
        sh.text((right + 2, P(0, zmax)[1] + 1), f"top +{zmax:.2f}", 2.0, "start")
    a, b = P(min(s[1] for s in spans), 0), P(max(s[2] for s in spans), 0)
    yd = gy + 9
    sh.line((min(a[0], b[0]), yd), (max(a[0], b[0]), yd), w=0.25)
    sh.text(((a[0] + b[0]) / 2, yd - 1.2), f"{max(s[2] for s in spans) - min(s[1] for s in spans):.2f}", 2.6)
    scale_bar(sh, (DRAW[0] + 5, PAGE_H - 20), k)
    return sh.svg()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--year", type=int, default=None)
    args = ap.parse_args()
    full = load_model(args.project)
    errs = check(full)
    for e in errs:
        print("ERROR:", e)
    if errs:
        sys.exit(1)
    print("building.json OK")
    if args.check:
        return
    year = args.year if args.year is not None else full["meta"].get("year")
    model = at_year(full, year)
    out = Path(args.project) / "05_blueprints"
    out.mkdir(exist_ok=True)
    suffix = f"_{year}" if year is not None else ""
    written = []
    for f in model["floors"]:
        written.append((out / f"plan_{f['id']}{suffix}.svg", plan_sheet(model, f, year)))
    if model["roofs"]:
        written.append((out / f"plan_roof{suffix}.svg", roof_plan_sheet(model, year)))
    for name, walls in facades(model).items():
        written.append((out / f"elevation_{name}{suffix}.svg",
                        elevation_sheet(model, walls[0].get("facade_name", name), walls, year)))
    for fn, svg in written:
        fn.write_text(svg, encoding="utf-8")
        print("wrote", fn)


if __name__ == "__main__":
    main()
