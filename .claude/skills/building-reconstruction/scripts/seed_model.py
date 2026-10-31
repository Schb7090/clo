#!/usr/bin/env python3
"""Seed building.json from the OSM footprint: floors, exterior walls, a roof.

Usage: seed_model.py projects/<slug> [--floors N] [--storey 4.2] [--tolerance 0.3] [--force]

Reads 04_model/footprint_osm.json (from fetch_open_data.py). Simplifies the
outline (Douglas–Peucker, --tolerance metres), orients it counter-clockwise,
and writes one exterior wall per edge per floor (facade id E1, E2, … so all
storeys of one façade share an elevation sheet). Floor count comes from
--floors, else OSM building:levels; storey height from --storey, else OSM
height / levels, else 4.0 m. Roof: flat at the eaves (grade D) — replace it
with real roof parts once photos are analysed.
Grades: wall positions B (footprint), heights C, everything typological D.
Refuses to overwrite a model that already has walls unless --force.
"""
import argparse
import json
import math
from pathlib import Path

from geometry import poly_area


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    seg = math.dist(a, b) or 1e-9
    def d(p):
        return abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / seg
    i, dmax = max(((i, d(p)) for i, p in enumerate(pts[1:-1], 1)), key=lambda t: t[1])
    if dmax <= tol:
        return [a, b]
    return simplify(pts[:i + 1], tol)[:-1] + simplify(pts[i:], tol)


def signed_area(pts):
    return sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--floors", type=int)
    ap.add_argument("--storey", type=float)
    ap.add_argument("--tolerance", type=float, default=0.3)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    project = Path(args.project)
    fp = json.loads((project / "04_model/footprint_osm.json").read_text(encoding="utf-8"))
    model_path = project / "04_model/building.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if model.get("walls") and not args.force:
        raise SystemExit("building.json already has walls; use --force to replace them.")

    poly = [tuple(p) for p in fp["polygon"]]
    if len(poly) > 1 and math.dist(poly[0], poly[-1]) < 1e-6:
        poly = poly[:-1]
    # Douglas–Peucker on an open chain: split the ring at its farthest vertex from vertex 0
    far = max(range(len(poly)), key=lambda i: math.dist(poly[0], poly[i]))
    ring = simplify(poly[:far + 1], args.tolerance)[:-1] + simplify(poly[far:] + [poly[0]], args.tolerance)[:-1]
    if signed_area(ring) < 0:
        ring = ring[::-1]
    ring = [[round(x, 2), round(y, 2)] for x, y in ring]
    tags = fp.get("tags", {})

    def num(v):
        try:
            return float(str(v).split()[0].replace(",", "."))
        except (ValueError, IndexError):
            return None

    height = num(tags.get("height"))
    osm_levels = int(num(tags.get("building:levels")) or 0)
    levels = args.floors or osm_levels
    if levels:
        storey = args.storey or (round(height / levels, 2) if height else 4.2)
    else:  # no level count anywhere: typical Budapest 19th c. storey, levels from height if known
        storey = args.storey or 4.2
        levels = max(1, round(height / storey)) if height else 3
        print(f"WARNING: no building:levels in OSM and no --floors; guessed {levels} floors of {storey} m"
              + (f" from height {height} m (OSM height may include towers/domes)" if height else "")
              + ". Count storeys on photos and rerun with --floors/--storey --force.")
    if storey > 6.5:
        print(f"WARNING: storey height {storey} m is implausible; check OSM height/levels, pass --storey.")
    src_id = "S_OSM"
    sources = [s for s in model.get("sources", []) if s["id"] != src_id]
    sources.append({"id": src_id, "title": "OpenStreetMap building footprint and tags", "grade": "B",
                    "url": fp.get("url", "https://www.openstreetmap.org/")})
    names = ["Ground floor"] + [f"{i}. emelet" for i in range(1, levels)]
    floors, walls = [], []
    for i in range(levels):
        fid = f"F{i}"
        floors.append({"id": fid, "name": names[i], "z": round(i * storey, 2), "height": storey,
                       "slab": 0.35, "outline": ring})
        thick = max(0.45, 0.9 - 0.15 * i)
        for j in range(len(ring)):
            a, b = ring[j], ring[(j + 1) % len(ring)]
            if math.dist(a, b) < 0.3:
                continue
            walls.append({"id": f"W{i}E{j + 1}", "name": f"Façade E{j + 1} — {names[i]}", "floor": fid,
                          "facade": f"E{j + 1}", "facade_name": f"Façade E{j + 1}", "from": a, "to": b,
                          "thickness": round(thick, 2), "confidence": "B", "sources": [src_id],
                          "notes": "position from OSM footprint; thickness and storey height are typological (C/D)"})
    eaves = round(levels * storey, 2)
    model.update({"sources": sources, "floors": floors, "walls": walls, "openings": [], "rooms": [], "stairs": [],
                  "roofs": [{"id": "RF1", "type": "flat", "footprint": ring, "eaves": eaves, "confidence": "D",
                             "sources": [], "notes": "placeholder; replace with real roof parts"}]})
    model.pop("roof", None)
    for k in ("name", "architect", "built"):
        if not model["meta"].get(k):
            model["meta"][k] = {"name": tags.get("name"), "architect": tags.get("architect"),
                                "built": tags.get("start_date") or tags.get("construction_date")}[k] or model["meta"].get(k)
    model_path.write_text(json.dumps(model, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Seeded {levels} floors × {len(walls) // levels} walls, storey {storey} m, eaves +{eaves}; "
          f"outline {len(poly)} → {len(ring)} vertices, area {poly_area(ring):.0f} m².")


if __name__ == "__main__":
    main()
