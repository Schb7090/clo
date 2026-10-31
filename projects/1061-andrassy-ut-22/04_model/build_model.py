#!/usr/bin/env python3
"""Generate building.json for the Hungarian State Opera House (Andrássy út 22).

Run from the repository root:
  python3 projects/1061-andrassy-ut-22/04_model/build_model.py

All geometry is defined in the building frame (u = rear → front along the
axis, v = across from the Hajós u. side to the Dalszínház u. side) with the
values recorded in 03_analysis/dimensions.md, then rotated into the OSM local
frame (x east, y north) so plans carry a true north arrow.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
FP = json.loads((HERE / "footprint_osm.json").read_text(encoding="utf-8"))

# ---------- frame: OSM axis (S2) ----------
P = FP["polygon"][:-1] if FP["polygon"][0] == FP["polygon"][-1] else FP["polygon"]
i = max(range(len(P)), key=lambda k: math.dist(P[k], P[(k + 1) % len(P)]))
ANG = math.atan2(P[(i + 1) % len(P)][1] - P[i][1], P[(i + 1) % len(P)][0] - P[i][0])
C, S = math.cos(-ANG), math.sin(-ANG)
Q = [(x * C - y * S, x * S + y * C) for x, y in P]
UMIN, VMIN = min(q[0] for q in Q), min(q[1] for q in Q)
CA, SA = math.cos(ANG), math.sin(ANG)


def W(u, v):
    """building frame (u, v) → OSM local plan coordinates (x east, y north)."""
    a, b = u + UMIN, v + VMIN
    return [round(a * CA - b * SA, 3), round(a * SA + b * CA, 3)]


UDIR_DEG = math.degrees(ANG)          # +u direction (towards Andrássy út)

# ---------- levels (S4/S5) ----------
FLOORS = [("F0", "Földszint (ground)", 0.0, 6.4), ("F1", "Félemelet (mezzanine)", 6.4, 3.4),
          ("F2", "I. emelet (piano nobile)", 9.8, 7.5), ("F3", "II. emelet", 17.3, 4.0),
          ("F4", "Attika (above main cornice)", 21.3, 6.1), ("F5", "High block top storey", 27.4, 5.4)]
THICK = {"F0": 1.2, "F1": 1.1, "F2": 1.0, "F3": 0.9, "F4": 0.8, "F5": 0.8}

# exterior ring from OSM in (u, v), counter-clockwise check below (S2)
RING = [(90.9, 51.14), (94.63, 51.14), (94.63, 41.78), (108.28, 41.78), (108.28, 10.96), (94.64, 10.95),
        (94.64, 1.76), (91.71, 1.76), (91.7, 0.4), (82.25, 0.4), (82.25, 1.37), (15.1, 1.37), (15.1, 0.0),
        (5.17, 0.0), (5.16, 1.89), (1.69, 1.89), (1.69, 10.91), (0.0, 10.9), (0.0, 42.59), (1.67, 42.59),
        (1.67, 50.91), (5.34, 50.91), (5.33, 53.2), (13.88, 53.2), (13.88, 51.02), (82.77, 51.03),
        (82.78, 53.17), (90.9, 53.18)]


def ccw(ring):
    a = sum(ring[k - 1][0] * ring[k][1] - ring[k][0] * ring[k - 1][1] for k in range(len(ring))) / 2
    return ring if a > 0 else ring[::-1]


RING = ccw(RING)

model = {
    "meta": {"name": "Magyar Állami Operaház (Hungarian State Opera House)", "address": "Andrássy út 22., Budapest",
             "postal": "1061", "district": "VI. kerület", "hrsz": None, "country": "HU",
             "lat": FP["origin"][0], "lon": FP["origin"][1], "year": 1884,
             "state": "as built 1884 (year slider: 1884 → today)", "architect": "Ybl Miklós",
             "built": "1875–1884 (opened 27 Sep 1884)",
             "disclaimer": "Reconstruction from Ybl's 1879 plans, archive photos and OSM; massing and main spaces, not a survey.",
             "plan_rotation_deg": round(-UDIR_DEG, 3),          # front (Andrássy út) to the right
             "frame": {"u_axis_deg_from_east": round(UDIR_DEG, 3),
                       "note": "u = rear (Lázár u.) → front (Andrássy út); v = Hajós u. side → Dalszínház u. side"}},
    "sources": [], "floors": [], "walls": [], "openings": [], "rooms": [], "stairs": [], "roofs": [], "ornaments": [],
}
SRC = {"S2": ("OSM building way/24000390", "B", "https://www.openstreetmap.org/way/24000390"),
       "S3": ("Ybl: Földszint alaprajza 1879, BTM KM ÉGY 65.048.7", "A", "https://ybl.bparchiv.hu/hu/foldszint-alaprajza"),
       "S4": ("Ybl: Oldalhomlokzat c.1879, BTM KM ÉGY 3262", "A", "https://ybl.bparchiv.hu/hu/oldalomolokzat"),
       "S5": ("Ybl: Főhomlokzat c.1879, BTM KM ÉGY 3261", "A", "https://ybl.bparchiv.hu/hu/fohomlokzat-35"),
       "S7": ("Hosszmetszet, Kozmata print, BTM KM ÉGY 51.718.8", "A", "https://ybl.bparchiv.hu/hu/keresztmetszet"),
       "S9": ("Tetőfedés felülnézet 1879, BTM KM ÉGY 76.180", "A", "https://ybl.bparchiv.hu/hu/tetofedes-felulnezet"),
       "S10": ("Divald: Andrássy úti főhomlokzat 1883 (Rozinay_97)", "B", "https://ybl.bparchiv.hu/hu/andrassy-uti-fohomlokzat"),
       "S11": ("Urbán N.: Főhomlokzat c.1960, HU_BFL_XV_17_e_306_2242_002", "B", "https://ybl.bparchiv.hu/hu/fohomlokzat-16"),
       "S12": ("KÖZTI 1969 façade photos, HU_BFL_XV_17_e_306_2242", "B", "https://ybl.bparchiv.hu/hu/hajos-utcai-homlokzat"),
       "S14": ("Szobrok az Operaház homlokzatán (opera.hu)", "B", "https://www.opera.hu/hu/hirek/szobrok_az_operahaz_homlokzatan/"),
       "S15": ("Magyar Állami Operaház — hu.wikipedia", "C", "https://hu.wikipedia.org/wiki/Magyar_%C3%81llami_Operah%C3%A1z"),
       "S16": ("Wellmann Nóra: Az Épület (opera.hu)", "B", "https://www.opera.hu/hu/hirek/wellmann_nora_az_epulet/"),
       "S18": ("Szfinxek — Köztérkép", "C", "https://www.kozterkep.hu/4073/szfinxek"),
       "S19": ("A View on Cities: State Opera House", "C", "https://aviewoncities.com/budapest/state-opera-house")}
model["sources"] = [{"id": k, "title": t, "grade": g, "url": u} for k, (t, g, u) in SRC.items()]

for fid, name, z, h in FLOORS:
    f = {"id": fid, "name": name, "z": z, "height": h, "slab": 0.35}
    if fid in ("F0", "F1", "F2", "F3", "F4"):
        f["outline"] = [W(*p) for p in RING]
    else:
        f["outline"] = [W(*p) for p in [(20.1, 11.1), (77.3, 11.1), (77.3, 42.1), (20.1, 42.1)]]
    model["floors"].append(f)

WALL_UV = {}


def facade_of(a, b):
    du, dv = b[0] - a[0], b[1] - a[1]
    nu, nv = dv, -du                      # right-hand normal = outward for a CCW ring
    if abs(nu) >= abs(nv):
        return ("FRONT", "Andrássy út (main) façade") if nu > 0 else ("REAR", "Lázár utca (rear) façade")
    return ("SIDE_D", "Dalszínház utca side façade") if nv > 0 else ("SIDE_H", "Hajós utca side façade")


def add_wall(wid, fid, a, b, conf, srcs, interior=False, notes="", thick=None, z=None):
    fac, facname = facade_of(a, b)
    w = {"id": wid, "name": f"{'Interior' if interior else facname} {wid}", "floor": fid, "from": W(*a), "to": W(*b),
         "thickness": thick or (0.8 if interior else THICK[fid]), "confidence": conf, "sources": srcs,
         "material": "brick; ashlar limestone façade" if not interior else "brick", "notes": notes}
    if interior:
        w["interior"] = True
    else:
        w["facade"], w["facade_name"] = fac, facname
    if z:
        w["z0"], w["z1"] = z
    model["walls"].append(w)
    WALL_UV[wid] = (a, b)
    return wid


def add_open(wid, center_uv, typ, width, sill, height, conf, srcs, oid=None, notes=""):
    a, b = WALL_UV[wid]
    L = math.dist(a, b)
    t = ((center_uv[0] - a[0]) * (b[0] - a[0]) + (center_uv[1] - a[1]) * (b[1] - a[1])) / L
    off = round(t - width / 2, 3)
    if off < 0.2 or off + width > L - 0.2:
        return None
    oid = oid or f"O_{wid}_{len([o for o in model['openings'] if o['wall'] == wid]) + 1}"
    model["openings"].append({"id": oid, "wall": wid, "type": typ, "offset": off, "width": width, "sill": sill,
                              "height": height, "confidence": conf, "sources": srcs, "notes": notes})
    return oid


def on_seg(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


# regular window rows per floor (S4 rhythm ≈ 3.9 m; sill/height from S4 rows)
ROWS = {"F0": [(1.5, 2.4, 3.0)], "F1": [(1.2, 0.6, 1.7)], "F2": [(1.2, 0.5, 1.8), (1.5, 3.1, 3.6)], "F3": [(1.2, 0.6, 1.8)]}


def is_front_block_face(a, b):
    return abs(a[0] - 108.28) < 0.05 and abs(b[0] - 108.28) < 0.05


def is_pavilion_front(a, b):
    return abs(a[0] - 94.635) < 0.05 and abs(b[0] - 94.635) < 0.05 and max(abs(a[1] - b[1]), 0) > 5


def side_porch(a, b):
    return abs(a[1] - b[1]) < 0.05 and (a[1] < 2 or a[1] > 50) and min(a[0], b[0]) < 41 and max(a[0], b[0]) > 58


# ---------- exterior walls F0–F3 (OSM ring, S2) with openings (S4, S5, S10) ----------
for fid, _, z, h in FLOORS[:4]:
    for k in range(len(RING)):
        a, b = RING[k], RING[(k + 1) % len(RING)]
        L = math.dist(a, b)
        if L < 0.3:
            continue
        wid = add_wall(f"W{fid[1]}_{k + 1:02d}", fid, a, b, "B", ["S2", "S4", "S5"],
                       notes="position from OSM footprint; storey heights from Ybl elevations")
        if is_front_block_face(a, b):
            if fid == "F0":
                for j, vc in enumerate((20.9, 26.4, 31.9)):
                    add_open(wid, (108.28, vc), "arch", 3.4, 0.0, 5.4, "B", ["S5", "S10"], f"O_ENTR_{j + 1}",
                             "main entrance arches under the carriage porch")
                add_open(wid, (108.28, 15.2), "niche", 2.4, 0.8, 4.2, "B", ["S10", "S14"], "N_ERKEL", "Erkel niche (left, S19)")
                add_open(wid, (108.28, 37.6), "niche", 2.4, 0.8, 4.2, "B", ["S10", "S14"], "N_LISZT", "Liszt niche (right, S19)")
            elif fid == "F2":
                for j in range(5):
                    add_open(wid, (108.28, 26.4 + (j - 2) * 4.2), "arch", 3.0, 0.4, 6.4, "B", ["S5", "S10"],
                             f"O_LOGGIA_{j + 1}", "foyer loggia arch")
                add_open(wid, (108.28, 13.6), "niche", 1.6, 1.4, 3.8, "B", ["S10", "S14"], "N_MUSE_FL")
                add_open(wid, (108.28, 39.2), "niche", 1.6, 1.4, 3.8, "B", ["S10", "S14"], "N_MUSE_FR")
            continue
        if is_pavilion_front(a, b):
            mid = on_seg(a, b, 0.5)
            spec = {"F0": ("door", 2.4, 0.0, 4.6), "F1": ("window", 1.2, 0.6, 1.7),
                    "F2": ("arch", 2.8, 0.6, 5.8), "F3": ("window", 1.2, 0.6, 1.8)}[fid]
            add_open(wid, mid, spec[0], spec[1], spec[2], spec[3], "B", ["S5", "S10"],
                     notes="side entrance with pediment" if fid == "F0" else "")
            continue
        if side_porch(a, b) and fid == "F0":
            for j, uc in enumerate((44.0, 49.35, 54.7)):
                add_open(wid, (uc, a[1]), "arch", 3.6, 0.0, 5.2, "B", ["S3", "S4"], f"O_{wid}_PORCH{j + 1}",
                         "carriage porch arch")
            for uc in [u for u in (17.0, 20.9, 24.8, 28.7, 32.6, 36.5, 60.5, 64.4, 68.3, 72.2, 76.1, 80.0)]:
                for wdt, sill, ht in ROWS[fid]:
                    add_open(wid, (uc, a[1]), "window", wdt, sill, ht, "B", ["S4"])
            continue
        n = int(L // 3.9)
        if n < 1:
            continue
        for j in range(n):
            c = on_seg(a, b, (j + 0.5) / n)
            for wdt, sill, ht in ROWS[fid]:
                add_open(wid, c, "window", wdt, sill, ht, "B" if L > 8 else "C", ["S4", "S12"],
                         notes="" if L > 8 else "short segment; rhythm inferred")
    # front block side faces get the single arched bay seen on S10
    # (handled by the regular rows above; F2 arch added here)
for k in range(len(RING)):
    a, b = RING[k], RING[(k + 1) % len(RING)]
    if abs(a[0] - b[0]) > 13 and abs(a[1] - b[1]) < 0.05 and abs(a[1] - 41.78) < 0.05 or \
       abs(a[0] - b[0]) > 13 and abs(a[1] - b[1]) < 0.05 and abs(a[1] - 10.955) < 0.05:
        wid = f"W2_{k + 1:02d}"
        model["openings"] = [o for o in model["openings"] if o["wall"] != wid]
        add_open(wid, on_seg(a, b, 0.5), "arch", 2.6, 0.5, 5.6, "B", ["S10"], notes="arched window, front block side")

# muse niches on the pavilion side faces (Thalia / Melpomene) — replace the F2 tall window at mid-face
for k in range(len(RING)):
    a, b = RING[k], RING[(k + 1) % len(RING)]
    if abs(a[1] - b[1]) < 0.05 and (abs(a[1] - 0.4) < 0.05 or abs(a[1] - 53.175) < 0.05) and min(a[0], b[0]) > 80:
        wid = f"W2_{k + 1:02d}"
        model["openings"] = [o for o in model["openings"] if o["wall"] != wid]
        side = "H" if a[1] < 1 else "D"
        add_open(wid, on_seg(a, b, 0.5), "niche", 1.6, 1.4, 3.8, "B", ["S4", "S14"], f"N_MUSE_{side}",
                 notes="muse niche on the pavilion side face (S4 shows a figure niche)")

# ---------- attic storey F4 (21.3–27.4) ----------
def rect_walls(prefix, fid, u0, u1, v0, v1, conf, srcs, z=None, skip=()):
    pts = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]      # CCW in (u, v)
    ids = []
    for k in range(4):
        if k in skip:
            continue
        ids.append(add_wall(f"{prefix}{k + 1}", fid, pts[k], pts[(k + 1) % 4], conf, srcs, z=z))
    return ids


attic_front = rect_walls("A4F_", "F4", 82.25, 94.64, 0.4, 53.18, "B", ["S4", "S5", "S10"])
rear_attic = rect_walls("A4R_", "F4", 0.0, 15.1, 0.0, 53.2, "B", ["S4", "S12"])
side_proj_h = rect_walls("A4SH_", "F4", 36.1, 58.7, 1.37, 11.1, "B", ["S4"], z=(21.3, 27.0))
side_proj_d = rect_walls("A4SD_", "F4", 36.1, 58.7, 42.1, 51.03, "B", ["S4"], z=(21.3, 27.0))
high4 = rect_walls("H4_", "F4", 20.1, 77.3, 11.1, 42.1, "B", ["S3", "S4", "S5"])
# attic storey on the front block, set back behind a narrow balustraded terrace (S10 detail, S5, S11)
front_attic = rect_walls("A4C_", "F4", 94.64, 106.0, 12.2, 40.5, "B", ["S5", "S10", "S11"])
high5 = rect_walls("H5_", "F5", 20.1, 77.3, 11.1, 42.1, "B", ["S4", "S5", "S7"])

# attic windows (S10: windows between the statue pilasters; S4: 5 windows on side projections)
front_attic_wall = "A4F_2"            # u = 94.64 face
for vc in (5.7, 47.6):
    add_open(front_attic_wall, (94.64, vc), "window", 1.3, 1.0, 2.4, "B", ["S10"])
for vc in (16.4, 21.6, 31.2, 36.4):     # 4 attic windows + central inscription panel (S10)
    add_open("A4C_2", (106.0, vc), "window", 1.4, 1.0, 2.6, "B", ["S10"])
for wid in (side_proj_h[0], side_proj_d[2]):
    a, b = WALL_UV[wid]
    for j in range(5):
        add_open(wid, on_seg(a, b, (j + 0.5) / 5), "window", 1.4, 1.2, 2.6, "B", ["S4"])
for wid in rear_attic:
    a, b = WALL_UV[wid]
    n = int(math.dist(a, b) // 3.9)
    for j in range(n):
        add_open(wid, on_seg(a, b, (j + 0.5) / n), "window", 1.2, 1.0, 2.0, "C", ["S4", "S12"])
for wid in (high5[0], high5[2]):     # long sides of the high block (S4 attic window row)
    a, b = WALL_UV[wid]
    n = int(math.dist(a, b) // 5.2)
    for j in range(n):
        add_open(wid, on_seg(a, b, (j + 0.5) / n), "window", 1.4, 1.6, 1.6, "B", ["S4"])
a, b = WALL_UV[high5[1]]              # front face of the high block above the hall roof (S11)
for j in range(4):
    add_open(high5[1], on_seg(a, b, (j + 1.5) / 6), "window", 1.6, 1.4, 2.2, "B", ["S11"])

# ---------- interior (S3) ----------
CU, CV, RIN, ROUT = 62.2, 26.46, 10.6, 15.2
for fid, _, z, h in FLOORS[:4]:
    n = fid[1]
    add_wall(f"I{n}_STR", fid, (20.1, 41.1), (20.1, 10.45), "B", ["S3"], interior=True, notes="rear stage wall")
    add_wall(f"I{n}_STL", fid, (20.1, 10.45), (45.4, 10.45), "B", ["S3"], interior=True, notes="stage side wall")
    add_wall(f"I{n}_STD", fid, (45.4, 41.1), (20.1, 41.1), "B", ["S3"], interior=True, notes="stage side wall")
    add_wall(f"I{n}_PRH", fid, (45.4, 10.45), (45.4, 18.2), "B", ["S3"], interior=True, notes="proscenium wall")
    add_wall(f"I{n}_PRD", fid, (45.4, 32.6), (45.4, 41.1), "B", ["S3"], interior=True, notes="proscenium wall")
    add_wall(f"I{n}_RH", fid, (45.4, CV - ROUT), (CU, CV - ROUT), "B", ["S3"], interior=True, notes="auditorium ring")
    add_wall(f"I{n}_RD", fid, (CU, CV + ROUT), (45.4, CV + ROUT), "B", ["S3"], interior=True, notes="auditorium ring")
    seg = 10
    for s in range(seg):
        t0, t1 = -math.pi / 2 + math.pi * s / seg, -math.pi / 2 + math.pi * (s + 1) / seg
        add_wall(f"I{n}_ARC{s + 1:02d}", fid, (CU + ROUT * math.cos(t0), CV + ROUT * math.sin(t0)),
                 (CU + ROUT * math.cos(t1), CV + ROUT * math.sin(t1)), "B", ["S3"], interior=True,
                 notes="horseshoe outer (box corridor) wall, 10-segment approximation")
    if fid in ("F0", "F1", "F2"):
        add_wall(f"I{n}_HR", fid, (83.2, 40.1), (83.2, 13.1), "B", ["S3"], interior=True, notes="staircase hall rear wall")
        add_wall(f"I{n}_HF", fid, (96.5, 12.5), (96.5, 40.2), "B", ["S3"], interior=True,
                 notes="staircase hall / vestibule wall")
        if fid == "F0":
            add_open(f"I{n}_HF", (96.5, 26.4), "arch", 8.0, 0.0, 5.6, "B", ["S3"], notes="open colonnade to the staircase")

# rooms (S3, S16)
def R(rid, fid, name, uv):
    model["rooms"].append({"id": rid, "floor": fid, "name": name, "polygon": [W(*p) for p in uv]})


R("R_STAGE", "F0", "Színpad (stage)", [(20.6, 10.95), (44.9, 10.95), (44.9, 40.6), (20.6, 40.6)])
arc = [(CU + RIN * math.cos(t), CV + RIN * math.sin(t)) for t in [-math.pi / 2 + math.pi * s / 12 for s in range(13)]]
R("R_AUD", "F0", "Nézőtér, földszint (parterre)", [(46.5, 17.6)] + arc[:1] + arc[1:] + [(46.5, 35.3)])
R("R_HALL", "F0", "Díszlépcsőház (grand staircase)", [(83.6, 13.5), (96.1, 13.5), (96.1, 39.7), (83.6, 39.7)])
R("R_VEST", "F0", "Előcsarnok (vestibule)", [(96.9, 12.5), (104.0, 12.5), (104.0, 40.2), (96.9, 40.2)])
R("R_FOYER", "F2", "Foyer (two-storey, behind the loggia)", [(96.9, 12.3), (106.8, 12.3), (106.8, 40.4), (96.9, 40.4)])
R("R_STAGE2", "F2", "Színpad (stage, upper)", [(20.6, 10.95), (44.9, 10.95), (44.9, 40.6), (20.6, 40.6)])

# grand staircase: two flights from the vestibule towards the auditorium (S3, S16)
back = (UDIR_DEG + 180) % 360
for sid, vstart in (("ST_GRAND_H", 19.1), ("ST_GRAND_D", 38.6)):
    model["stairs"].append({"id": sid, "floor": "F0", "type": "straight", "start": W(96.0, vstart), "angle": back,
                            "width": 5.0, "going": 0.36, "steps": 32, "rise": 5.3, "confidence": "B",
                            "sources": ["S3", "S16"],
                            "notes": "two flights of the díszlépcső; rise to the parterre level (stage floor +5.29 m, S15) approximated"})

# ---------- roofs ----------
def rect(u0, u1, v0, v1):
    return [W(u0, v0), W(u1, v0), W(u1, v1), W(u0, v1)]


def roof(rid, typ, conf, srcs, notes="", period=None, **kw):
    r = {"id": rid, "type": typ, "confidence": conf, "sources": srcs, "notes": notes, **kw}
    if period:
        r["period"] = period
    model["roofs"].append(r)


roof("RF_HIGH", "mansard", "B", ["S4", "S5", "S7", "S11"], footprint=rect(20.1, 77.3, 11.1, 42.1),
     eaves=33.4, **{"break": 42.2}, break_inset=3.2, ridge=42.2,
     notes="curved roof over auditorium + stage modelled as mansard with flat top at +42.2")
for rid, uc in (("RF_LANT_AUD", 62.2), ("RF_LANT_STG", 32.7)):
    oct_ = [W(uc + 1.6 * math.cos(math.pi / 8 + k * math.pi / 4), CV + 1.6 * math.sin(math.pi / 8 + k * math.pi / 4))
            for k in range(8)]
    roof(rid, "pyramid", "C" if rid.endswith("STG") else "B", ["S7"] + ([] if rid.endswith("STG") else ["S10", "S11"]),
         footprint=oct_, eaves=44.8, ridge=47.0,
         notes="lantern cap; " + ("seen on S7 only" if rid.endswith("STG") else "visible on 1883 and c.1960 photos"))
roof("RF_HALL", "hip", "B", ["S5", "S11"], footprint=rect(80.5, 94.64, 11.1, 42.1), eaves=27.4, ridge=30.7,
     notes="curved roof with dormers over the grand staircase hall")
roof("RF_PAV_FH", "hip", "C", ["S4", "S5"], footprint=rect(82.25, 94.64, 0.4, 11.1), eaves=27.4, ridge=30.8,
     notes="S4 32.0 vs S5 29.7 → mean")
roof("RF_PAV_FD", "hip", "C", ["S4", "S5"], footprint=rect(82.25, 94.64, 42.1, 53.18), eaves=27.4, ridge=30.8)
roof("RF_REAR", "hip", "C", ["S4", "S12"], footprint=rect(0.0, 15.1, 0.0, 53.2), eaves=27.4, ridge=31.3)
for side, (v0, v1) in (("H", (1.37, 11.1)), ("D", (42.1, 51.03))):
    roof(f"RF_WING_{side}1", "hip", "C", ["S4"], footprint=rect(15.1, 36.1, v0, v1), eaves=21.3, ridge=25.5,
         notes="low roof behind the balustrade")
    roof(f"RF_WING_{side}2", "hip", "B", ["S4"], footprint=rect(36.1, 58.7, v0, v1), eaves=27.0, ridge=30.3,
         notes="central side projection with attic")
    roof(f"RF_WING_{side}3", "hip", "C", ["S4"], footprint=rect(58.7, 82.25, v0, v1), eaves=21.3, ridge=25.5)
roof("RF_FRONT", "flat", "B", ["S10", "S11"], footprint=rect(94.64, 108.28, 10.95, 41.78), eaves=21.3,
     notes="terrace around the front attic; the composer statues stand on it")
roof("RF_FRONT_ATTIC", "flat", "B", ["S5", "S10", "S11"], footprint=rect(94.64, 106.0, 12.2, 40.5), eaves=27.4,
     notes="top of the front attic storey")
roof("RF_PORCH", "flat", "B", ["S4", "S10", "S11"], footprint=rect(108.28, 114.78, 17.4, 35.4), eaves=9.8,
     notes="carriage porch terrace; depth 6.5 m from S4, width from photos (C)")
roof("RF_SPORCH_H", "flat", "B", ["S3", "S4"], footprint=rect(40.4, 58.3, -3.93, 1.37), eaves=10.3)
roof("RF_SPORCH_D", "flat", "B", ["S3", "S4"], footprint=rect(40.4, 58.3, 51.03, 56.33), eaves=10.3)

# ---------- ornaments ----------
def orn(oid, typ, name, wall, uv, z, size, conf, srcs, notes="", period=None, **kw):
    o = {"id": oid, "type": typ, "name": name, "wall": wall, "position": W(*uv) + [z], "size": size,
         "confidence": conf, "sources": srcs, "notes": notes, **kw}
    if period:
        o["period"] = period
    model["ornaments"].append(o)


# 16 composer statues on the terraces above the main cornice (S10 1883 detail): left to right as seen
# from Andrássy út. Count = A (S14); this distribution = D (the 1883 photo shows 13–15 from its viewpoint).
pos = [("A4F_1", (88.5, -0.2)), ("A4F_2", (95.3, 3.5)), ("A4F_2", (95.3, 8.0)), ("A4C_1", (101.0, 11.5))] + \
      [("A4C_2", (106.7, 13.4 + j * 3.7)) for j in range(8)] + \
      [("A4C_3", (101.0, 41.2)), ("A4F_2", (95.3, 45.0)), ("A4F_2", (95.3, 49.5)), ("A4F_3", (88.5, 53.6))]
ORIG = [("Guido d'Arezzo", "Donáth Gyula"), ("Palestrina", "Kiss György"), ("Jacopo Peri", "Kiss György"),
        ("Orlando di Lasso", "Donáth Gyula"), ("Pergolesi", "Donáth Gyula"), ("Lully", "Brestyánszky Béla"),
        ("Cherubini", "Strobl Alajos"), ("Spontini", "Strobl Alajos"), ("Haydn", "Huszár Adolf"),
        ("Gluck", "Szász Gyula"), ("Mozart", "Szász Gyula"), ("Beethoven", "Huszár Adolf"),
        ("Weber", "Brestyánszky Béla"), ("Meyerbeer", "Szász Gyula"), ("Rossini", "Brestyánszky Béla"),
        ("Wagner", "Huszár Adolf")]
NEW = [("Monteverdi", "Ispánki József"), ("A. Scarlatti", "Győry Dezső"), ("Gluck", "Győry Dezső"),
       ("Mozart", "Marton László"), ("Beethoven", "Marton László"), ("Rossini", "Tar István"),
       ("Donizetti", "Tar István"), ("Glinka", "Mikus Sándor"), ("Wagner", "Mikus Sándor"), ("Verdi", "Pátzay Pál"),
       ("Gounod", "Pátzay Pál"), ("Bizet", "Váradi Sándor"), ("Musorgszkij", "Váradi Sándor"),
       ("Csajkovszkij", "Antal Károly"), ("Moniuszko", "Antal Károly"), ("Smetana", "Ispánki József")]
for j, ((wall, uv), (who, by)) in enumerate(zip(pos, ORIG)):
    orn(f"CO{j + 1:02d}", "statue", f"{who} (original)", wall, uv, 21.3, [0.8, 0.7, 2.2], "C", ["S10", "S14", "S15"],
        "Sóskút limestone, set Sept 1881, removed after 1939; subject/sculptor A (S14/S15), position D "
        "(original order not documented)", period=[1881, 1939], sculptor=by, material="Sóskút limestone")
for j, ((wall, uv), (who, by)) in enumerate(zip(pos, NEW)):
    orn(f"CN{j + 1:02d}", "statue", who, wall, uv, 21.3, [0.8, 0.7, 2.2], "C", ["S14", "S15"],
        "Dec 1966 (S14) / 1965 (S15); order left→right A (S14), exact spot along the attic D", period=[1966, None],
        sculptor=by, material="limestone (Bulgarian per S14, Süttő per S15)")
F0_FRONT = next(w["id"] for w in model["walls"] if w["floor"] == "F0" and is_front_block_face(*WALL_UV[w["id"]]))
F2_FRONT = F0_FRONT.replace("W0_", "W2_")
orn("ST_ERKEL", "statue", "Erkel Ferenc (seated)", F0_FRONT, (108.0, 15.2), 1.2, [1.6, 1.2, 2.6], "B", ["S14", "S15", "S19"],
    "Strobl Alajos, limestone, c.1882–84; left of the entrance per S19 (C)", sculptor="Strobl Alajos", material="limestone")
orn("ST_LISZT", "statue", "Liszt Ferenc (seated)", F0_FRONT, (108.0, 37.6), 1.2, [1.6, 1.2, 2.6], "B", ["S14", "S15", "S19"],
    "Strobl Alajos, limestone; head lost to a hit in WWII and restored (S14); right of entrance per S19 (C)",
    sculptor="Strobl Alajos", material="limestone")
orn("MU_ERATO", "statue", "Erato (muse)", F2_FRONT, (107.9, 13.6), 11.2, [1.0, 0.7, 3.0], "C", ["S14", "S15"],
    "Fessler Leo (Vienna); which front niche holds Erato vs Terpsichore not documented (D)", sculptor="Fessler Leo")
orn("MU_TERPS", "statue", "Terpsichore (muse)", F2_FRONT, (107.9, 39.2), 11.2, [1.0, 0.7, 3.0], "C", ["S14", "S15"],
    "Fessler Leo (Vienna)", sculptor="Fessler Leo")
for oid, name, by, wid_k, uvz in (("MU_THALIA", "Thalia (muse)", "Donáth Gyula", "H", (87.0, 0.0)),
                                  ("MU_MELPO", "Melpomene (muse)", "Brestyánszky Albert (1883 caption; 'Béla' in S14/S15)", "D", (86.5, 53.6))):
    wall = next(o["wall"] for o in model["openings"] if o["id"] == f"N_MUSE_{wid_k}")
    orn(oid, "statue", name, wall, uvz, 11.2, [1.0, 0.7, 3.0], "C", ["S4", "S14", "S15"],
        "side-façade muse; side assignment D (Melpomene photographed with the Liszt niche, S12/Rozinay_99)", sculptor=by)
P0 = [w["id"] for w in model["walls"] if w["floor"] == "F0" and is_pavilion_front(*WALL_UV[w["id"]])]
orn("SPHINX_H", "other", "Sphinx with mask (Hajós u. side)", P0[0], (97.8, 6.0), 0.6, [1.1, 3.0, 1.7], "C", ["S14", "S15", "S18"],
    "Strobl Alajos, Carrara marble (S14/S15; S18 says limestone), installed 20 Sep 1884", sculptor="Strobl Alajos",
    period=[1884, None])
orn("SPHINX_D", "other", "Sphinx with laurel wreath (Dalszínház u. side)", P0[-1], (97.8, 46.4), 0.6, [1.1, 3.0, 1.7], "C",
    ["S14", "S15", "S18"], "Strobl Alajos", sculptor="Strobl Alajos", period=[1884, None])
for j, vc in enumerate((17.9, 34.9)):
    orn(f"PUTTO_{j + 1}", "statue", "Winged bronze putto with lamp", F0_FRONT, (114.3, vc), 9.8, [0.7, 0.7, 2.0], "B",
        ["S10", "S11", "S15"], "on the porch terrace corners", material="bronze")
for j, vc in enumerate((14.6, 38.2)):
    orn(f"CANDEL_{j + 1}", "other", "Cast-iron candelabrum", F0_FRONT, (116.8, vc), 0.0, [0.9, 0.9, 5.0], "C", ["S10", "S11"],
        "four large lamp posts at the carriage entrance (S15); two outer ones modelled")
for j, vc in enumerate((17.9, 23.2, 29.6, 34.9)):
    orn(f"PIER_F{j + 1}", "pilaster", "Front porch pier", F0_FRONT, (114.2, vc), 0.0, [1.3, 1.3, 9.8], "B", ["S3", "S10"],
        "three arches of the carriage porch")
for side, vo in (("H", -3.4), ("D", 55.8)):
    for j, uc in enumerate((40.9, 46.7, 52.4, 57.8)):
        wall = next(w["id"] for w in model["walls"] if w["floor"] == "F0" and side_porch(*WALL_UV[w["id"]])
                    and ((WALL_UV[w["id"]][0][1] < 2) == (side == "H")))
        orn(f"PIER_{side}{j + 1}", "pilaster", "Side carriage porch pier", wall, (uc, vo), 0.0, [1.2, 1.2, 10.3], "B",
            ["S3", "S4"])
for oid, uc in (("LANTERN_AUD", 62.2), ("LANTERN_STG", 32.7)):
    orn(oid, "other", "Roof lantern drum", "H5_2", (uc, CV), 42.2, [3.2, 3.2, 2.6], "C" if "STG" in oid else "B",
        ["S7"] + ([] if "STG" in oid else ["S10", "S11"]), "glazed lantern on the high roof")

out = HERE / "building.json"
out.write_text(json.dumps(model, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"wrote {out}: {len(model['walls'])} walls, {len(model['openings'])} openings, {len(model['roofs'])} roofs, "
      f"{len(model['ornaments'])} ornaments, {len(model['rooms'])} rooms")
