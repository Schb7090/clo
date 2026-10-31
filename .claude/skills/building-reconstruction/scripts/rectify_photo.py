#!/usr/bin/env python3
"""Rectify a façade photo with a four-point homography and measure on it.

Usage:
  rectify_photo.py photo.jpg out.png --points "x,y x,y x,y x,y" --width 24.0 --height 12.6
      [--extend L,R,T,B] [--ppm 50] [--measure "label:x,y:x,y" ...] [--check "x,y:x,y:metres" ...]

--points   pixel corners of a rectangle that lies in the façade plane, in the
           order top-left, top-right, bottom-right, bottom-left. Pick them with
           assets/pick_points.html.
--width/--height  real size of that rectangle in metres (e.g. façade width
           from the OSM footprint, cornice height from a permit plan).
--extend   metres to include beyond the rectangle (left, right, top, bottom).
--measure  two pixel points in the ORIGINAL photo; prints their distance and
           the height of each above the rectangle's bottom edge, in metres.
--check    a known distance; prints the residual (use a second reference
           length that was not used for the rectangle).
Writes out.png with a 1 m grid and out.json with the homography, scale and
all measurements. Measurements are only valid for points in the façade plane.
Requires numpy and Pillow.
"""
import argparse
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def parse_pt(s):
    x, y = s.split(",")
    return float(x), float(y)


def homography(src, dst):
    """3x3 H with dst ~ H @ src for four point pairs (DLT, h33 = 1)."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    h = np.linalg.solve(np.array(A, float), np.array(b, float))
    return np.append(h, 1).reshape(3, 3)


def apply(H, p):
    v = H @ np.array([p[0], p[1], 1.0])
    return v[0] / v[2], v[1] / v[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out")
    ap.add_argument("--points", required=True)
    ap.add_argument("--width", type=float, required=True)
    ap.add_argument("--height", type=float, required=True)
    ap.add_argument("--extend", default="0,0,0,0")
    ap.add_argument("--ppm", type=float, default=50, help="output pixels per metre")
    ap.add_argument("--measure", action="append", default=[])
    ap.add_argument("--check", action="append", default=[])
    args = ap.parse_args()

    pts = [parse_pt(p) for p in args.points.split()]
    if len(pts) != 4:
        raise SystemExit("--points needs exactly four x,y pairs (TL TR BR BL)")
    eL, eR, eT, eB = (float(v) for v in args.extend.split(","))
    k = args.ppm
    # metric frame: origin at the rectangle's top-left, x right, y down (metres)
    rect_m = [(0, 0), (args.width, 0), (args.width, args.height), (0, args.height)]
    to_out = lambda X, Y: ((X + eL) * k, (Y + eT) * k)
    H_out2in = homography([to_out(*p) for p in rect_m], pts)
    H_in2m = homography(pts, rect_m)

    img = Image.open(args.image).convert("RGB")
    W, Hh = round((args.width + eL + eR) * k), round((args.height + eT + eB) * k)
    coeffs = (H_out2in / H_out2in[2, 2]).reshape(-1)[:8]
    out = img.transform((W, Hh), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC, fillcolor=(255, 255, 255))

    d = ImageDraw.Draw(out)
    font = ImageFont.load_default()
    for X in range(-math.floor(eL), math.floor(args.width + eR) + 1):
        x = (X + eL) * k
        d.line([(x, 0), (x, Hh)], fill=(255, 0, 0) if X % 5 == 0 else (255, 150, 150), width=1)
        if X % 5 == 0:
            d.text((x + 2, 2), f"{X} m", fill=(200, 0, 0), font=font)
    for Z in range(-math.floor(eB), math.floor(args.height + eT) + 1):  # height above rectangle bottom
        y = (args.height - Z + eT) * k
        d.line([(0, y), (W, y)], fill=(0, 0, 255) if Z % 5 == 0 else (150, 150, 255), width=1)
        if Z % 5 == 0:
            d.text((2, y - 12), f"+{Z} m", fill=(0, 0, 200), font=font)
    d.rectangle([to_out(0, 0), to_out(args.width, args.height)], outline=(0, 160, 0), width=2)

    report = {"image": args.image, "points_px": pts, "rect_m": [args.width, args.height],
              "extend_m": [eL, eR, eT, eB], "px_per_m": k,
              "homography_in_to_m": H_in2m.tolist(), "measurements": [], "checks": []}
    for spec in args.measure:
        label, a, b = spec.split(":")
        A, B = apply(H_in2m, parse_pt(a)), apply(H_in2m, parse_pt(b))
        dist = math.dist(A, B)
        za, zb = args.height - A[1], args.height - B[1]
        report["measurements"].append({"label": label, "a_m": A, "b_m": B, "distance_m": round(dist, 3),
                                       "dx_m": round(abs(B[0] - A[0]), 3), "dz_m": round(abs(zb - za), 3),
                                       "z_a_m": round(za, 3), "z_b_m": round(zb, 3)})
        print(f"{label}: {dist:.3f} m (horizontal {abs(B[0] - A[0]):.3f}, vertical {abs(zb - za):.3f}); "
              f"heights above base +{za:.3f} / +{zb:.3f}")
        pa, pb = to_out(*A), to_out(*B)
        d.line([pa, pb], fill=(0, 140, 0), width=3)
        d.text(((pa[0] + pb[0]) / 2 + 4, (pa[1] + pb[1]) / 2), f"{label} {dist:.2f} m", fill=(0, 110, 0), font=font)
    for spec in args.check:
        a, b, known = spec.split(":")
        dist = math.dist(apply(H_in2m, parse_pt(a)), apply(H_in2m, parse_pt(b)))
        res = dist - float(known)
        report["checks"].append({"known_m": float(known), "measured_m": round(dist, 3), "residual_m": round(res, 3),
                                 "residual_pct": round(100 * res / float(known), 2)})
        print(f"check: known {float(known):.3f} m, measured {dist:.3f} m, residual {res:+.3f} m ({100 * res / float(known):+.1f} %)")
    out.save(args.out)
    with open(args.out.rsplit(".", 1)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"wrote {args.out} ({W}×{Hh} px, {k:g} px/m) and its .json")


if __name__ == "__main__":
    main()
