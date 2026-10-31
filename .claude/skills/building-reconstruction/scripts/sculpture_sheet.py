#!/usr/bin/env python3
"""Build a printable reference sheet for one statue or ornament.

Usage: sculpture_sheet.py projects/<slug> <ornament-id>

Reads   04_model/building.json (the ornament record and sources)
        07_sculpture/<id>/images.csv   file,item_date,source_id,viewpoint,notes
        07_sculpture/<id>/images/      the image files listed in images.csv
        07_sculpture/<id>/dossier.md   optional; shown as preformatted text
Writes  07_sculpture/<id>/reference_sheet.html (images ordered by date)
"""
import argparse
import csv
import json
from html import escape
from pathlib import Path

GRADE = {"A": "#2e7d32", "B": "#1565c0", "C": "#ef6c00", "D": "#c62828"}
LABEL = {"A": "documented", "B": "measured", "C": "inferred", "D": "speculative"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("id")
    args = ap.parse_args()
    project = Path(args.project)
    model = json.loads((project / "04_model/building.json").read_text(encoding="utf-8"))
    orn = next((o for o in model.get("ornaments", []) if o["id"] == args.id), None)
    if not orn:
        raise SystemExit(f"No ornament {args.id} in building.json")
    folder = project / "07_sculpture" / args.id
    (folder / "images").mkdir(parents=True, exist_ok=True)
    csv_path = folder / "images.csv"
    if not csv_path.exists():
        csv_path.write_text("file,item_date,source_id,viewpoint,notes\n", encoding="utf-8")
    with csv_path.open(encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: r.get("item_date") or "9999")
    sources = {s["id"]: s for s in model.get("sources", [])}

    def src(sid):
        s = sources.get(sid)
        if not s:
            return escape(sid or "—")
        t = escape(s["title"])
        return f'{escape(sid)}: <a href="{escape(s["url"])}">{t}</a>' if s.get("url") else f"{escape(sid)}: {t}"

    g = orn.get("confidence", "D")
    facts = "".join(f"<tr><th>{escape(k)}</th><td>{escape(json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else ("—" if v is None else str(v)))}</td></tr>"
                    for k, v in orn.items() if k not in ("id", "sources"))
    facts += "<tr><th>sources</th><td>" + "<br>".join(src(s) for s in orn.get("sources", [])) + "</td></tr>"
    cards = "".join(
        f'<figure><img src="images/{escape(r["file"])}" alt="{escape(r.get("viewpoint", ""))}">'
        f'<figcaption><b>{escape(r.get("item_date") or "undated")}</b> · {escape(r.get("viewpoint", ""))}<br>'
        f'{src(r.get("source_id"))}<br>{escape(r.get("notes", ""))}</figcaption></figure>' for r in rows)
    dossier = folder / "dossier.md"
    dossier_html = f"<h2>Dossier</h2><pre>{escape(dossier.read_text(encoding='utf-8'))}</pre>" if dossier.exists() else ""
    mesh_note = ""
    if orn.get("model"):
        mesh_note = (f'<p class="warn">3D mesh: <code>{escape(orn["model"])}</code>. Grade {g}. A mesh made from one '
                     "photo shows the front outline only; depth and back are invented.</p>")
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(args.id)} reference sheet</title>
<style>
 :root {{ --bg:#fff; --ink:#1d1d1f; --muted:#666; --line:#ddd; }}
 @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#16171a; --ink:#ececef; --muted:#9a9aa3; --line:#33363c; }} }}
 :root[data-theme="dark"] {{ --bg:#16171a; --ink:#ececef; --muted:#9a9aa3; --line:#33363c; }}
 body {{ background:var(--bg); color:var(--ink); font:14px/1.45 system-ui, sans-serif; margin:0 auto; padding:24px 16px; max-width:1100px; }}
 h1 {{ margin:0 0 4px; font-size:22px; }} .sub {{ color:var(--muted); }}
 .grade {{ display:inline-block; color:#fff; background:{GRADE.get(g, '#888')}; padding:2px 8px; border-radius:4px; font-weight:700; }}
 table {{ border-collapse:collapse; margin:16px 0; width:100%; }} th, td {{ text-align:left; border-top:1px solid var(--line); padding:4px 8px; vertical-align:top; }}
 th {{ width:140px; color:var(--muted); font-weight:500; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:14px; }}
 figure {{ margin:0; border:1px solid var(--line); border-radius:6px; overflow:hidden; }}
 figure img {{ width:100%; display:block; background:#eee; }} figcaption {{ padding:8px; font-size:12px; }}
 .warn {{ border-left:4px solid #c62828; padding:6px 10px; }}
 pre {{ white-space:pre-wrap; border:1px solid var(--line); padding:10px; border-radius:6px; }}
 @media print {{ body {{ max-width:none; }} }}
</style></head><body>
<h1>{escape(orn.get('name', args.id))} <span class="grade">{g} — {LABEL.get(g, '')}</span></h1>
<div class="sub">{escape(args.id)} · {escape(orn.get('type', ''))} · {escape(model['meta'].get('name', ''))}, {escape(model['meta'].get('address', ''))}</div>
{mesh_note}
<table>{facts}</table>
<h2>Images ({len(rows)}), oldest first</h2>
<div class="grid">{cards or '<p>No images listed in images.csv yet.</p>'}</div>
{dossier_html}
</body></html>
"""
    out = folder / "reference_sheet.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
