#!/usr/bin/env python3
"""Create the project folder for one Budapest building reconstruction.

Usage: new_project.py "<address>" "<postal>" [--hrsz 12345] [--root projects]

Budapest postal codes are 1XXY: the middle two digits are the district
(1061 -> VI. kerület). Other codes are refused: the source catalogue and
search plan of this skill cover Budapest only.
"""
import argparse
import datetime
import json
import re
import unicodedata
from pathlib import Path

SOURCE_LOG_HEADER = "id,title,repository,url,item_date,type,license,accessed,grade,used_for,notes\n"
CATALOG_HEADER = "id,source_id,file,item_date,viewpoint,shows,quality,notes\n"


ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV",
         "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII"]


def budapest_district(postal):
    """1XXY -> (number, 'VI. kerület'); None if not a Budapest code."""
    if not (len(postal) == 4 and postal.isdigit() and postal[0] == "1"):
        return None
    n = int(postal[1:3])
    return (n, f"{ROMAN[n]}. kerület") if 1 <= n <= 23 else None


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("address")
    ap.add_argument("postal")
    ap.add_argument("--hrsz", default="", help="parcel number (helyrajzi szám), if known")
    ap.add_argument("--root", default="projects")
    args = ap.parse_args()

    postal = args.postal.strip()
    district = budapest_district(postal)
    if not district:
        raise SystemExit(f"{postal} is not a Budapest postal code (1XXY, district 01–23).")
    address = args.address if "budapest" in args.address.lower() else f"{args.address}, Budapest"
    slug = slugify(f"{postal} {args.address}")
    root = Path(args.root) / slug
    if root.exists():
        raise SystemExit(f"{root} already exists; not overwriting.")

    for sub in ["00_intake", "01_sources/raw", "02_images", "03_analysis",
                "04_model", "05_blueprints", "06_3d", "07_sculpture"]:
        (root / sub).mkdir(parents=True)

    today = datetime.date.today().isoformat()
    files = {
        "00_intake/request.md": f"# Request\n\n- Address: {address}\n- Postal code: {postal}\n"
                                f"- District: {district[1]}\n- Parcel (hrsz.): {args.hrsz or '(find)'}\n- Opened: {today}\n\n"
                                "## Intake answers\n- States to reconstruct (years): \n- User's files / subscriptions (Arcanum ADT, Mapillary token, own photos, scans): \n"
                                "- Scope (whole building / street façade / interior): \n",
        "03_analysis/identity.md": "# Identity\n\n| Item | Value | Source | Grade |\n|---|---|---|---|\n"
                                   "| Official / popular name | | | |\n| Former names | | | |\n| Current address | | | |\n"
                                   "| Former addresses (street renames, renumbering) | | | |\n| Parcel number (hrsz.), current and historic | | | |\n"
                                   "| Architect(s) | | | |\n| Builder / contractor | | | |\n| Commissioning owner | | | |\n"
                                   "| Permit year / completion year | | | |\n| Style | | | |\n| Protection (műemlék / fővárosi / kerületi helyi védelem) | | | |\n",
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
        "meta": {"name": "", "address": address, "postal": postal, "district": district[1],
                 "hrsz": args.hrsz or None, "country": "HU", "lat": None, "lon": None, "year": None, "state": "",
                 "architect": None, "built": "",
                 "disclaimer": "Reconstruction from listed sources; not a measured survey."},
        "sources": [], "floors": [], "walls": [], "openings": [],
        "roofs": [], "rooms": [], "stairs": [], "ornaments": [],
    }
    (root / "04_model/building.json").write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")
    print(root)


if __name__ == "__main__":
    main()
