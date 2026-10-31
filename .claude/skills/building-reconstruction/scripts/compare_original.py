#!/usr/bin/env python3
"""Build a page that overlays an archival plan scan on a generated sheet.

Usage: compare_original.py projects/<slug> <scan image> <generated sheet.svg> [--title "..."]

The scan is copied into 05_blueprints/originals/. On the page you click two
matching points on the scan and two on the generated sheet (e.g. two building
corners); the page fits scale, rotation and offset, and shows the scan over
the sheet with an opacity slider. Deviations listed in
05_blueprints/deviations.csv (element,original,reconstruction,difference,note)
are shown as a table below. Output: 05_blueprints/comparison_<sheet>.html
"""
import argparse
import csv
import json
import shutil
from html import escape
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("scan")
    ap.add_argument("sheet")
    ap.add_argument("--title", default="")
    args = ap.parse_args()
    bp = Path(args.project) / "05_blueprints"
    (bp / "originals").mkdir(parents=True, exist_ok=True)
    scan = Path(args.scan)
    dest = bp / "originals" / scan.name
    if scan.resolve() != dest.resolve():
        shutil.copy2(scan, dest)
    sheet = Path(args.sheet)
    sheet_rel = sheet.resolve().relative_to(bp.resolve()).as_posix()
    dev = bp / "deviations.csv"
    if not dev.exists():
        dev.write_text("element,original,reconstruction,difference,note\n", encoding="utf-8")
    with dev.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    table = "".join("<tr>" + "".join(f"<td>{escape(r.get(k) or '')}</td>" for k in
                    ["element", "original", "reconstruction", "difference", "note"]) + "</tr>" for r in rows)
    title = args.title or f"Original plan vs reconstruction — {sheet.stem}"
    cfg = json.dumps({"scan": f"originals/{scan.name}", "sheet": sheet_rel, "key": f"cmp:{sheet.stem}:{scan.name}"})
    html = TEMPLATE.replace("{{TITLE}}", escape(title)).replace("{{CFG}}", cfg).replace(
        "{{ROWS}}", table or '<tr><td colspan="5">No deviations recorded yet (05_blueprints/deviations.csv).</td></tr>')
    out = bp / f"comparison_{sheet.stem}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plan Comparison</title>
<style>
 :root { --bg:#f4f2ee; --panel:#fff; --ink:#1d1d1f; --muted:#6b6b70; --line:#dcd8d0; }
 @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#16171a; --panel:#1f2125; --ink:#ececef; --muted:#9a9aa3; --line:#33363c; } }
 :root[data-theme="dark"] { --bg:#16171a; --panel:#1f2125; --ink:#ececef; --muted:#9a9aa3; --line:#33363c; }
 body { margin:0; background:var(--bg); color:var(--ink); font:14px/1.4 system-ui, sans-serif; }
 header { padding:12px 16px; background:var(--panel); border-bottom:1px solid var(--line); }
 h1 { font-size:17px; margin:0 0 6px; }
 .bar { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
 button { font:inherit; padding:4px 10px; }
 .muted { color:var(--muted); }
 main { padding:16px; }
 .pair { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
 @media (max-width:800px) { .pair { grid-template-columns:1fr; } }
 .pane { position:relative; background:#fff; border:1px solid var(--line); }
 .pane img { width:100%; display:block; cursor:crosshair; }
 .pane h2 { position:absolute; left:6px; top:4px; margin:0; font-size:12px; background:rgba(255,255,255,.85); color:#333; padding:1px 6px; border-radius:3px; }
 .pt { position:absolute; width:12px; height:12px; margin:-6px 0 0 -6px; border-radius:50%; border:2px solid #fff; pointer-events:none; }
 #overlay { position:relative; overflow:hidden; background:#fff; border:1px solid var(--line); display:none; }
 #overlay img { position:absolute; left:0; top:0; transform-origin:0 0; max-width:none; }
 table { border-collapse:collapse; width:100%; margin-top:16px; background:var(--panel); }
 th, td { border:1px solid var(--line); padding:4px 8px; text-align:left; }
</style></head>
<body>
<header>
 <h1>{{TITLE}}</h1>
 <div class="bar">
  <span id="step" class="muted"></span>
  <button id="reset">Reset points</button>
  <button id="mode">Overlay</button>
  <label>Scan opacity <input id="op" type="range" min="0" max="100" value="55"></label>
 </div>
</header>
<main>
 <div class="pair" id="pair">
  <div class="pane" id="paneScan"><h2>Archival scan</h2><img id="scan" alt="archival plan"></div>
  <div class="pane" id="paneSheet"><h2>Reconstruction</h2><img id="sheet" alt="generated plan"></div>
 </div>
 <div id="overlay"><img id="oSheet" alt=""><img id="oScan" alt=""></div>
 <p id="fit" class="muted"></p>
 <h2>Recorded deviations</h2>
 <table><tr><th>Element</th><th>Original</th><th>Reconstruction</th><th>Difference</th><th>Note</th></tr>{{ROWS}}</table>
</main>
<script>
const CFG = {{CFG}};
const $ = id => document.getElementById(id);
$('scan').src = $('oScan').src = CFG.scan;
$('sheet').src = $('oSheet').src = CFG.sheet;
let pts = { scan: [], sheet: [] };
try { pts = JSON.parse(localStorage.getItem(CFG.key)) || pts; } catch (e) {}
const COLORS = ['#e53935', '#1e88e5'];
function save() { try { localStorage.setItem(CFG.key, JSON.stringify(pts)); } catch (e) {} }
function next() { return pts.scan.length < 2 ? 'scan' : pts.sheet.length < 2 ? 'sheet' : null; }
function click(which, e) {
  if (next() !== which) return;
  const img = $(which), r = img.getBoundingClientRect(), s = img.naturalWidth / r.width;
  pts[which].push([(e.clientX - r.left) * s, (e.clientY - r.top) * s]); save(); draw();
}
$('scan').onclick = e => click('scan', e);
$('sheet').onclick = e => click('sheet', e);
$('reset').onclick = () => { pts = { scan: [], sheet: [] }; save(); draw(); };
$('op').oninput = () => $('oScan').style.opacity = $('op').value / 100;
let overlay = false;
$('mode').onclick = () => { overlay = !overlay; $('mode').textContent = overlay ? 'Side by side' : 'Overlay'; draw(); };
addEventListener('resize', draw);
// similarity transform scan->sheet from two point pairs (complex-number form)
function similarity() {
  const [p1, p2] = pts.scan, [q1, q2] = pts.sheet;
  const dpx = p2[0] - p1[0], dpy = p2[1] - p1[1], dqx = q2[0] - q1[0], dqy = q2[1] - q1[1];
  const den = dpx * dpx + dpy * dpy;
  const a = (dqx * dpx + dqy * dpy) / den, b = (dqy * dpx - dqx * dpy) / den;
  return { a, b, tx: q1[0] - (a * p1[0] - b * p1[1]), ty: q1[1] - (b * p1[0] + a * p1[1]) };
}
function draw() {
  for (const which of ['scan', 'sheet']) {
    const pane = which === 'scan' ? $('paneScan') : $('paneSheet');
    pane.querySelectorAll('.pt').forEach(n => n.remove());
    const img = $(which), s = img.getBoundingClientRect().width / (img.naturalWidth || 1);
    pts[which].forEach((p, i) => {
      const d = document.createElement('div'); d.className = 'pt'; d.style.background = COLORS[i];
      d.style.left = p[0] * s + 'px'; d.style.top = p[1] * s + 'px'; pane.append(d);
    });
  }
  const n = next();
  $('step').textContent = n ? `Click point ${pts[n].length + 1} of 2 on the ${n === 'scan' ? 'archival scan' : 'reconstruction'} (red, then blue; same features on both).`
                            : 'Aligned. Switch to Overlay to compare.';
  $('pair').style.display = overlay ? 'none' : '';
  $('overlay').style.display = overlay ? 'block' : 'none';
  if (overlay && !n) {
    const box = $('overlay'), W = $('oSheet').naturalWidth, H = $('oSheet').naturalHeight;
    const k = box.clientWidth / W;
    box.style.height = H * k + 'px';
    $('oSheet').style.width = W * k + 'px';
    const t = similarity();
    $('oScan').style.transform = `matrix(${t.a * k},${t.b * k},${-t.b * k},${t.a * k},${t.tx * k},${t.ty * k})`;
    $('oScan').style.opacity = $('op').value / 100;
    $('fit').textContent = `Fit: scale ${Math.hypot(t.a, t.b).toFixed(4)} sheet px per scan px, rotation ${(Math.atan2(t.b, t.a) * 180 / Math.PI).toFixed(2)}°.`;
  } else $('fit').textContent = '';
}
$('scan').onload = $('sheet').onload = draw;
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
