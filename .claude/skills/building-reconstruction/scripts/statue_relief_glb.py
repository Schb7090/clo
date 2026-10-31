#!/usr/bin/env python3
"""Turn a cut-out photo of a statue into a textured 2.5D relief mesh (GLB).

Usage:
  statue_relief_glb.py cutout.png out.glb --height 2.2 [--depth 0.5] [--grid 120]
                       [--threshold 40]

The input is a frontal photo of the figure with the background removed
(transparent PNG), or a photo on a plain background (then the background is
the colour of the corner pixels, removed by --threshold). Thickness is
inflated from the outline (distance to the edge), so the front shows the
photographed figure correctly and the depth and back are invented.
Evidence grade of the result: D (illustration). Requires numpy and Pillow.
"""
import argparse
import io
import json
import struct

import numpy as np
from PIL import Image


def load_mask(path, threshold, grid):
    img = Image.open(path).convert("RGBA")
    a = np.asarray(img).astype(np.float32)
    if a[..., 3].min() < 250:  # real transparency present
        mask = a[..., 3] > 128
    else:
        corners = np.stack([a[0, 0, :3], a[0, -1, :3], a[-1, 0, :3], a[-1, -1, :3]]).mean(0)
        mask = np.linalg.norm(a[..., :3] - corners, axis=-1) > threshold
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        raise SystemExit("No figure found in the image (mask is empty).")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    img = img.crop((x0, y0, x1, y1))
    mask = mask[y0:y1, x0:x1]
    h, w = mask.shape
    rows = grid
    cols = max(2, round(grid * w / h))
    small = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize((cols, rows), Image.BILINEAR)) > 127
    return img, small


def chamfer_distance(mask):
    """Distance (in cells) from each inside cell to the outside, two-pass chamfer 3-4."""
    INF = 10 ** 6
    h, w = mask.shape
    d = np.where(mask, INF, 0).astype(np.int64)
    d = np.pad(d, 1)  # border counts as outside
    for y in range(1, h + 1):
        for x in range(1, w + 1):
            if d[y, x]:
                d[y, x] = min(d[y, x], d[y - 1, x] + 3, d[y, x - 1] + 3, d[y - 1, x - 1] + 4, d[y - 1, x + 1] + 4)
    for y in range(h, 0, -1):
        for x in range(w, 0, -1):
            if d[y, x]:
                d[y, x] = min(d[y, x], d[y + 1, x] + 3, d[y, x + 1] + 3, d[y + 1, x + 1] + 4, d[y + 1, x - 1] + 4)
    return d[1:-1, 1:-1] / 3.0


def build_mesh(mask, height, depth):
    rows, cols = mask.shape
    dist = chamfer_distance(mask)
    m = dist.max()
    thick = np.where(mask, depth * np.sqrt(np.clip((dist - 1) / max(m - 1, 1e-6), 0, 1)), 0)
    s = height / (rows - 1)
    idx = -np.ones((rows, cols), dtype=np.int64)
    ys, xs = np.nonzero(mask)
    idx[ys, xs] = np.arange(len(ys))
    n = len(ys)
    X = (xs - (cols - 1) / 2) * s
    Y = (rows - 1 - ys) * s
    Z = thick[ys, xs] / 2
    pos = np.concatenate([np.stack([X, Y, Z], 1), np.stack([X, Y, -Z], 1)]).astype(np.float32)
    uv = np.stack([xs / (cols - 1), ys / (rows - 1)], 1)
    uvs = np.concatenate([uv, uv]).astype(np.float32)
    tris = []
    for y in range(rows - 1):
        for x in range(cols - 1):
            a, b, c, d = idx[y, x], idx[y, x + 1], idx[y + 1, x], idx[y + 1, x + 1]
            quad = [(a, c, b), (b, c, d)] if min(a, b, c, d) >= 0 else \
                   [t for t in [(a, c, b), (b, c, d), (a, c, d), (a, d, b)] if min(t) >= 0][:1]
            for t in quad:
                tris.append(t)                                   # front, counter-clockwise seen from +z
                tris.append((t[0] + n, t[2] + n, t[1] + n))      # back, reversed winding
    ind = np.array(tris, dtype=np.uint32).reshape(-1)
    # vertex normals
    nrm = np.zeros_like(pos)
    tri = ind.reshape(-1, 3)
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    for k in range(3):
        np.add.at(nrm, tri[:, k], fn)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    return pos, nrm.astype(np.float32), uvs, ind


def write_glb(path, pos, nrm, uv, ind, texture_png, extras):
    blobs, views, offset = [], [], 0

    def add(data, target=None):
        nonlocal offset
        b = data.tobytes() if hasattr(data, "tobytes") else data
        pad = (-len(b)) % 4
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(b), **({"target": target} if target else {})})
        blobs.append(b + b"\0" * pad)
        offset += len(b) + pad
        return len(views) - 1

    vp, vn, vt = add(pos, 34962), add(nrm, 34962), add(uv, 34962)
    vi, vimg = add(ind, 34963), add(texture_png)
    gltf = {
        "asset": {"version": "2.0", "generator": "building-reconstruction statue_relief_glb.py",
                  "extras": extras},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": extras.get("name", "statue")}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
                                    "indices": 3, "material": 0}]}],
        "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0,
                                                "roughnessFactor": 0.9}, "doubleSided": True}],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9729}],
        "images": [{"bufferView": vimg, "mimeType": "image/png"}],
        "accessors": [
            {"bufferView": vp, "componentType": 5126, "count": len(pos), "type": "VEC3",
             "min": pos.min(0).tolist(), "max": pos.max(0).tolist()},
            {"bufferView": vn, "componentType": 5126, "count": len(nrm), "type": "VEC3"},
            {"bufferView": vt, "componentType": 5126, "count": len(uv), "type": "VEC2"},
            {"bufferView": vi, "componentType": 5125, "count": len(ind), "type": "SCALAR"}],
        "bufferViews": views,
        "buffers": [{"byteLength": offset}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    bin_ = b"".join(blobs)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js)
        f.write(struct.pack("<I4s", len(bin_), b"BIN\0") + bin_)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out")
    ap.add_argument("--height", type=float, required=True, help="figure height in metres")
    ap.add_argument("--depth", type=float, default=None, help="max thickness in metres (default 0.25 × height)")
    ap.add_argument("--grid", type=int, default=120, help="vertical mesh resolution")
    ap.add_argument("--threshold", type=float, default=40, help="background colour distance (no-alpha images)")
    ap.add_argument("--name", default="statue")
    args = ap.parse_args()
    img, mask = load_mask(args.image, args.threshold, args.grid)
    pos, nrm, uv, ind = build_mesh(mask, args.height, args.depth or 0.25 * args.height)
    tex = img.copy()
    tex.thumbnail((1024, 1024))
    buf = io.BytesIO()
    tex.save(buf, "PNG")
    extras = {"name": args.name, "method": "2.5D relief inflated from one frontal photo",
              "grade": "D", "warning": "Depth and back side are invented; front outline follows the photo."}
    write_glb(args.out, pos, nrm, uv, ind, buf.getvalue(), extras)
    print(f"wrote {args.out}: {len(pos)} vertices, {len(ind) // 3} triangles (grade D illustration)")


if __name__ == "__main__":
    main()
