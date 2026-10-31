"""Shared model loading, validation and geometry for the generators.

Single source of truth for derived geometry (roof faces, stair steps), so the
blueprints and the 3D viewer always agree.
Plan coordinates: x east, y north, metres; z up from ±0.00.
"""
import copy
import json
import math
from pathlib import Path

GRADES = "ABCD"
ROOF_TYPES = {"flat", "gable", "hip", "mansard", "pyramid", "dome"}
OPENING_TYPES = {"window", "door", "arch", "niche", "shopfront"}


# ---------- loading ----------

def load_model(project):
    model = json.loads((Path(project) / "04_model/building.json").read_text(encoding="utf-8"))
    return normalize(model)


def normalize(model):
    """Fill defaults and accept the v1 single `roof` object."""
    m = copy.deepcopy(model)
    for k in ["sources", "floors", "walls", "openings", "ornaments", "rooms", "stairs"]:
        m[k] = m.get(k) or []
    roofs = m.get("roofs") or []
    if m.get("roof"):
        roofs = [dict(m["roof"], id=m["roof"].get("id", "roof"))] + roofs
    m["roofs"] = roofs
    m.pop("roof", None)
    return m


def exists(el, year):
    """True when the element exists in `year` (period = [from, to], either may be null)."""
    if year is None or not el.get("period"):
        return True
    a, b = (el["period"] + [None, None])[:2]
    return (a is None or a <= year) and (b is None or year <= b)


def at_year(model, year):
    if year is None:
        return model
    m = copy.deepcopy(model)
    for k in ["walls", "openings", "ornaments", "rooms", "stairs", "roofs"]:
        m[k] = [e for e in m[k] if exists(e, year)]
    walls = {w["id"] for w in m["walls"]}
    m["openings"] = [o for o in m["openings"] if o["wall"] in walls]
    return m


# ---------- basic helpers ----------

def wall_len(w):
    return math.dist(w["from"], w["to"])


def floor_by_id(model, fid):
    return next((f for f in model["floors"] if f["id"] == fid), None)


def wall_z(model, w):
    f = floor_by_id(model, w.get("floor"))
    z0 = w.get("z0", f["z"] if f else 0.0)
    z1 = w.get("z1", (f["z"] + f["height"]) if f else z0 + 3.0)
    return z0, z1


def poly_area(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2


def poly_centroid(pts):
    a = 0.0
    cx = cy = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if abs(a) < 1e-9:
        return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
    return [cx / (3 * a), cy / (3 * a)]


def floor_outline(model, floor):
    """Explicit floor outline, else the chain of exterior wall start points."""
    if floor.get("outline"):
        return floor["outline"]
    return [w["from"] for w in model["walls"] if w.get("floor") == floor["id"] and not w.get("interior")]


def building_centroid(model):
    pts = [p for w in model["walls"] if not w.get("interior") for p in (w["from"], w["to"])]
    if not pts:
        return [0.0, 0.0]
    return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]


# ---------- roofs ----------

def _v(a, b):
    return [b[0] - a[0], b[1] - a[1]]


def _add(a, *vs):
    return [a[0] + sum(v[0] for v in vs), a[1] + sum(v[1] for v in vs)]


def _scale(v, k):
    return [v[0] * k, v[1] * k]


def _unit(v):
    n = math.hypot(*v)
    return [v[0] / n, v[1] / n]


def _rect_long_first(fp):
    """Reorder a 4-point rectangle so p0→p1 is a long side."""
    p = [list(x) for x in fp]
    if math.dist(p[0], p[3]) > math.dist(p[0], p[1]):
        p = [p[1], p[2], p[3], p[0]]
    return p


def _hip_faces(rect, ze, zr, kind):
    p0, p1, p2, p3 = _rect_long_first(rect)
    e1, e2 = _v(p0, p1), _v(p0, p3)
    half = _scale(e2, 0.5)
    m0, m1 = _add(p0, half), _add(p1, half)
    if kind == "hip":
        d = _scale(_unit(e1), min(math.hypot(*e2) / 2, math.hypot(*e1) / 2 - 0.01))
        m0, m1 = _add(m0, d), _add(m1, _scale(d, -1))
    P = lambda q, z: [q[0], q[1], z]
    faces = [[P(p0, ze), P(p1, ze), P(m1, zr), P(m0, zr)],
             [P(p2, ze), P(p3, ze), P(m0, zr), P(m1, zr)],
             [P(p1, ze), P(p2, ze), P(m1, zr)],
             [P(p3, ze), P(p0, ze), P(m0, zr)]]
    return faces


def roof_faces(r):
    """List of planar faces, each a list of [x, y, z] points."""
    t = r.get("type", "flat")
    ze, zr = r.get("eaves", 0.0), r.get("ridge", r.get("eaves", 0.0))
    if t == "dome":
        cx, cy = r["center"]
        rx, ry = (r["radius"], r["radius"]) if not isinstance(r["radius"], list) else r["radius"]
        nlon, nlat = 32, 10
        ring = lambda k: [[cx + rx * math.cos(math.pi / 2 * k / nlat) * math.cos(2 * math.pi * j / nlon),
                           cy + ry * math.cos(math.pi / 2 * k / nlat) * math.sin(2 * math.pi * j / nlon),
                           ze + (zr - ze) * math.sin(math.pi / 2 * k / nlat)] for j in range(nlon)]
        faces = []
        for k in range(nlat):
            a, b = ring(k), ring(k + 1)
            for j in range(nlon):
                j2 = (j + 1) % nlon
                f = [a[j], a[j2], b[j2], b[j]] if k < nlat - 1 else [a[j], a[j2], b[j]]
                faces.append(f)
        return faces
    fp = r["footprint"]
    if t == "flat":
        return [[[p[0], p[1], ze] for p in fp]]
    if t == "pyramid":
        c = poly_centroid(fp)
        return [[[fp[i - 1][0], fp[i - 1][1], ze], [fp[i][0], fp[i][1], ze], [c[0], c[1], zr]] for i in range(len(fp))]
    if t in ("gable", "hip"):
        return _hip_faces(fp, ze, zr, t)
    if t == "mansard":
        zb = r["break"]
        inset = r.get("break_inset", 0.2 * min(math.dist(fp[0], fp[1]), math.dist(fp[0], fp[3])))
        p = _rect_long_first(fp)
        u1, u2 = _unit(_v(p[0], p[1])), _unit(_v(p[0], p[3]))
        q = [_add(p[0], _scale(u1, inset), _scale(u2, inset)), _add(p[1], _scale(u1, -inset), _scale(u2, inset)),
             _add(p[2], _scale(u1, -inset), _scale(u2, -inset)), _add(p[3], _scale(u1, inset), _scale(u2, -inset))]
        faces = [[[p[i][0], p[i][1], ze], [p[(i + 1) % 4][0], p[(i + 1) % 4][1], ze],
                  [q[(i + 1) % 4][0], q[(i + 1) % 4][1], zb], [q[i][0], q[i][1], zb]] for i in range(4)]
        if zr > zb + 1e-6:
            faces += _hip_faces(q, zb, zr, r.get("upper", "hip"))
        else:
            faces.append([[x, y, zb] for x, y in q])
        return faces
    raise ValueError(f"unknown roof type {t}")


# ---------- stairs ----------

def stair_steps(model, s):
    """Steps as {poly: 4 plan points, z0, z1} plus flight centre lines for arrows."""
    f = floor_by_id(model, s["floor"])
    z = f["z"] if f else 0.0
    rise = s.get("rise", f["height"] if f else 3.0)
    n = s["steps"]
    h = rise / n
    going, w = s["going"], s["width"]
    ang = math.radians(s.get("angle", 0))
    d = [math.cos(ang), math.sin(ang)]
    left = [-d[1], d[0]]
    steps, lines = [], []

    def flight(start, direction, count, k0):
        lat = [-direction[1], direction[0]]
        for i in range(count):
            a = _add(start, _scale(direction, i * going))
            b = _add(a, _scale(direction, going))
            steps.append({"poly": [a, b, _add(b, _scale(lat, w)), _add(a, _scale(lat, w))],
                          "z0": z, "z1": z + h * (k0 + i + 1)})
        mid = _scale(lat, w / 2)
        lines.append([_add(start, mid), _add(start, mid, _scale(direction, count * going))])

    if s.get("type", "straight") == "straight":
        flight(s["start"], d, n, 0)
    elif s["type"] == "dogleg":
        n1 = (n + 1) // 2
        gap = s.get("gap", 0.2)
        land = s.get("landing", w)
        flight(s["start"], d, n1, 0)
        end1 = _add(s["start"], _scale(d, n1 * going))
        lz = z + h * n1
        steps.append({"poly": [end1, _add(end1, _scale(d, land)), _add(end1, _scale(d, land), _scale(left, 2 * w + gap)),
                               _add(end1, _scale(left, 2 * w + gap))], "z0": z, "z1": lz, "landing": True})
        # second flight runs back on the left side, starting at the landing
        start2 = _add(end1, _scale(left, 2 * w + gap))
        back = _scale(d, -1)
        # flight() lays steps to the left of its direction; going back, left of `back` is right of `d`
        flight(start2, back, n - n1, n1)
    else:
        raise ValueError(f"unknown stair type {s['type']}")
    return steps, lines


# ---------- validation ----------

def check(model):
    errs = []
    ids = {}
    for kind in ["floors", "walls", "openings", "ornaments", "sources", "rooms", "stairs", "roofs"]:
        for el in model[kind]:
            if "id" not in el:
                errs.append(f"{kind}: element without id")
                continue
            if el["id"] in ids:
                errs.append(f"duplicate id {el['id']} ({kind} and {ids[el['id']]})")
            ids[el["id"]] = kind
    src = {s["id"] for s in model["sources"]}
    floors = {f["id"] for f in model["floors"]}
    walls = {w["id"]: w for w in model["walls"]}
    for el in model["walls"] + model["openings"] + model["ornaments"] + model["roofs"] + model["stairs"]:
        if el.get("confidence") not in tuple(GRADES):
            errs.append(f"{el.get('id')}: confidence must be A–D, got {el.get('confidence')!r}")
        for s in el.get("sources", []):
            if s not in src:
                errs.append(f"{el['id']}: unknown source {s}")
        if not el.get("sources") and el.get("confidence") in ("A", "B"):
            errs.append(f"{el['id']}: grade {el['confidence']} needs at least one source")
        p = el.get("period")
        if p is not None and (not isinstance(p, list) or len(p) != 2):
            errs.append(f"{el['id']}: period must be [from_year, to_year] (null allowed)")
    for w in walls.values():
        if w.get("floor") not in floors:
            errs.append(f"{w['id']}: unknown floor {w.get('floor')}")
        if wall_len(w) <= 0:
            errs.append(f"{w['id']}: zero length")
    for o in model["openings"]:
        w = walls.get(o.get("wall"))
        if not w:
            errs.append(f"{o['id']}: unknown wall {o.get('wall')}")
            continue
        if o.get("type") not in OPENING_TYPES:
            errs.append(f"{o['id']}: type must be one of {sorted(OPENING_TYPES)}")
        z0, z1 = wall_z(model, w)
        if o["offset"] < 0 or o["offset"] + o["width"] > wall_len(w) + 1e-6:
            errs.append(f"{o['id']}: does not fit along {w['id']} (length {wall_len(w):.2f})")
        if o["sill"] < 0 or o["sill"] + o["height"] > (z1 - z0) + 1e-6:
            errs.append(f"{o['id']}: taller than {w['id']} ({z1 - z0:.2f} m)")
    for r in model["ornaments"]:
        if r.get("wall") and r["wall"] not in walls:
            errs.append(f"{r['id']}: unknown wall {r['wall']}")
    for r in model["roofs"]:
        t = r.get("type")
        if t not in ROOF_TYPES:
            errs.append(f"{r['id']}: roof type must be one of {sorted(ROOF_TYPES)}")
        elif t in ("gable", "hip", "mansard") and len(r.get("footprint", [])) != 4:
            errs.append(f"{r['id']}: {t} needs a 4-point rectangular footprint (split L/U plans into parts)")
        elif t == "mansard" and "break" not in r:
            errs.append(f"{r['id']}: mansard needs 'break' (z of the slope change)")
        elif t == "dome" and ("center" not in r or "radius" not in r):
            errs.append(f"{r['id']}: dome needs center and radius")
        elif t in ("flat", "pyramid") and len(r.get("footprint", [])) < 3:
            errs.append(f"{r['id']}: {t} needs a footprint polygon")
    for r in model["rooms"]:
        if r.get("floor") not in floors:
            errs.append(f"{r['id']}: unknown floor {r.get('floor')}")
    for s in model["stairs"]:
        if s.get("floor") not in floors:
            errs.append(f"{s['id']}: unknown floor {s.get('floor')}")
        else:
            try:
                stair_steps(model, s)
            except (KeyError, ValueError) as e:
                errs.append(f"{s['id']}: {e}")
    return errs
