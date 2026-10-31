#!/usr/bin/env python3
"""Create the project folder for one building reconstruction.

Usage: new_project.py "<address>" "<postal>" [--country HU] [--root projects]
"""
import argparse
import datetime
import json
import re
import unicodedata
from pathlib import Path

SOURCE_LOG_HEADER = "id,title,repository,url,item_date,type,license,accessed,grade,used_for,notes\n"
CATALOG_HEADER = "id,source_id,file,item_date,viewpoint,shows,quality,notes\n"


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("address")
    ap.add_argument("postal")
    ap.add_argument("--country", default="")
    ap.add_argument("--root", default="projects")
    args = ap.parse_args()

    slug = slugify(f"{args.postal} {args.address}")
    root = Path(args.root) / slug
    if root.exists():
        raise SystemExit(f"{root} already exists; not overwriting.")

    for sub in ["00_intake", "01_sources/raw", "02_images", "03_analysis",
                "04_model", "05_blueprints", "06_3d", "07_sculpture"]:
        (root / sub).mkdir(parents=True)

    today = datetime.date.today().isoformat()
    files = {
        "00_intake/request.md": f"# Request\n\n- Address: {args.address}\n- Postal code: {args.postal}\n"
                                f"- Country: {args.country or '(infer)'}\n- Opened: {today}\n\n"
                                "## Intake answers\n- State to reconstruct: \n- User's files / subscriptions: \n- Scope: \n",
        "01_sources/source_log.csv": SOURCE_LOG_HEADER,
        "02_images/catalog.csv": CATALOG_HEADER,
        "03_analysis/timeline.md": "# Timeline\n\n| Date | Event | Source | Grade |\n|---|---|---|---|\n",
        "03_analysis/dimensions.md": "# Dimensions\n\n| Element | Value (m) | Method | Source | Grade |\n|---|---|---|---|---|\n",
        "03_analysis/conflicts.md": "# Conflicting evidence\n\n| Topic | Source A says | Source B says | Decision and reason |\n|---|---|---|---|\n",
        "REPORT.md": "# Report\n\n## Summary\n## Identity\n## Timeline\n## Sources by grade\n"
                     "## Found / not found\n## Open archive requests\n## Dimensions\n## Accuracy\n"
                     "## Uncertainties\n## Deliverables\n",
    }
    for rel, content in files.items():
        (root / rel).write_text(content, encoding="utf-8")

    model = {
        "meta": {"name": "", "address": args.address, "postal": args.postal,
                 "country": args.country, "lat": None, "lon": None, "state": "",
                 "architect": None, "built": "",
                 "disclaimer": "Reconstruction from listed sources; not a measured survey."},
        "sources": [], "floors": [], "walls": [], "openings": [],
        "roof": None, "ornaments": [],
    }
    (root / "04_model/building.json").write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")
    print(root)


if __name__ == "__main__":
    main()
