#!/usr/bin/env python3
"""Embed 04_model/building.json into the viewer template -> 06_3d/viewer.html.

Usage: build_viewer.py projects/<slug>

Ornament "model" paths are relative to the project folder; they are rewritten
relative to 06_3d/ so the viewer finds them (serve the project folder over
http for GLB files: `python3 -m http.server` from the project root).
"""
import argparse
import json
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets/viewer_template.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    project = Path(args.project)
    model = json.loads((project / "04_model/building.json").read_text(encoding="utf-8"))
    for o in model.get("ornaments") or []:
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
