#!/usr/bin/env python3
"""Embed 04_model/building.json into the viewer template -> 06_3d/viewer.html.

Usage: build_viewer.py projects/<slug>

Roof faces and stair steps are computed here (geometry.py) so the viewer and
the blueprints always show the same geometry. Ornament "model" paths are
relative to the project folder; they are rewritten relative to 06_3d/.
GLB files only load over http: run `python3 -m http.server` in the project
folder and open http://localhost:8000/06_3d/viewer.html.
"""
import argparse
import json
import sys
from pathlib import Path

from geometry import check, load_model, roof_faces, stair_steps

TEMPLATE = Path(__file__).resolve().parent.parent / "assets/viewer_template.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    project = Path(args.project)
    model = load_model(project)
    errs = check(model)
    if errs:
        print("\n".join("ERROR: " + e for e in errs))
        sys.exit(1)
    for r in model["roofs"]:
        r["_faces"] = [[[round(c, 4) for c in p] for p in f] for f in roof_faces(r)]
    for s in model["stairs"]:
        s["_steps"], s["_lines"] = stair_steps(model, s)
    for o in model["ornaments"]:
        if o.get("model") and not o["model"].startswith(("http://", "https://", "../")):
            o["model"] = "../" + o["model"]
    data = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*BUILDING_JSON*/", data)
    out = project / "06_3d/viewer.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
