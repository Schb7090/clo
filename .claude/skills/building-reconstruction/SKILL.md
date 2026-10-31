---
name: building-reconstruction
description: Reconstruct a historic Budapest building (17th–20th c.) from just an address and postal code (1XXY). Researches Budapest archives and open data (BFL building plans via Hungaricana, MÉM MDK, Arcanum ADT/MAPIRE, Fortepan, Egykor, Budapest100, OSM, Wikidata, Commons), rectifies façade photos to measure them, builds an evidence-graded and dated building model (building.json), generates SVG plans, roof plan and elevations per year, an interactive Three.js 3D model with per-element isolation, section cut and year slider, an overlay against found original plans, and statue dossiers with optional relief meshes. Use when the user gives a Budapest address and asks for the history, original plans, blueprints, 3D model or statues of a building.
---

# Budapest building reconstruction from an address

Input: **address + Budapest postal code** (1XXY; the middle digits are the
district). Optional: parcel number (hrsz.), years to reconstruct, the user's
files. Output: a project folder with sources, analysis, `building.json`,
blueprints, a 3D viewer, statue dossiers and a report. Every claim and
dimension carries a **source** and a **grade** (A documented, B measured,
C inferred, D speculative; see `references/evidence-and-confidence.md`).

The original blueprint exists only if an archive holds it. Say so plainly,
and write the exact scan order when it is not online.

All scripts are in `scripts/` (Python 3.9+, standard library; numpy and
Pillow for photo and statue tools). Run them from the repository root.

## Phase 0 — Intake (one message, then work)
Ask only what the user has not said:
1. Which **years/states**: as built, a later year, today, or several.
2. **Access and files**: Arcanum ADT login, Mapillary token, own photos,
   archive scans, the hrsz.
3. **Scope**: whole building, street façade only, interior too.

Then: `python3 scripts/new_project.py "<street and number>" <postal> [--hrsz N]`
→ `projects/<postal>-<street>/` with `00_intake … 07_sculpture`, templates for
`identity.md`, `timeline.md`, `dimensions.md`, `conflicts.md`, `REPORT.md`.

## Phase 1 — Locate, identify, seed
1. `python3 scripts/fetch_open_data.py projects/<slug>`: Nominatim geocode,
   OSM footprint and tags, Commons photos within 150 m, Wikidata items within
   100 m, and `01_sources/search_plan.md` with ready queries. Blocked
   services are reported; do those steps by hand and log them.
2. `python3 scripts/seed_model.py projects/<slug> [--floors N --storey H]`:
   floors and exterior walls from the footprint. Fix the storey count from
   photos and rerun with `--force` when it warns.
3. Fill `03_analysis/identity.md`: names, former addresses and street names,
   hrsz., architect, builder, owner, dates, protection level.

## Phase 2 — Archive and literature sweep
Work through `search_plan.md` and `references/sources.md` in order:
original plans (BFL Tervtár by hrsz., MÉM MDK), press and journals (Arcanum
ADT, Hungaricana), address books, photos (Fortepan, Egykor, Commons,
Budapest100, PestBuda), maps (MAPIRE, BFL parcel maps), sculpture
(Köztérkép, press).
- Run searches in parallel; repeat street searches with every former street
  name, and in German before 1918.
- Log each hit in `source_log.csv` **before** using it; quote the passage and
  page for text.
- Arcanum ADT full text needs a subscription: use only what you can read;
  ask the user to export pages. Never claim content you did not read.
- Google Street View: look only (browser tool if available), record the
  imagery date; never download.
- Plan not online → write the BFL / MÉM MDK request (fond, hrsz., address,
  years) in `REPORT.md` under "Open archive requests".

## Phase 3 — Images and measurement
1. Catalogue every image in `02_images/catalog.csv` (date, source, viewpoint,
   what it shows) and order by date; changes go to `timeline.md`.
2. Rectify the best façade photos (`references/measurement.md`):
   `assets/pick_points.html` → `scripts/rectify_photo.py` with `--check`.
3. Every number goes into `dimensions.md` with method, source and grade;
   disagreements into `conflicts.md` with the decision.

## Phase 4 — Model (`04_model/building.json`)
Follow `references/building-schema.md`: floors (with outlines), exterior
walls and partitions, openings (window, door, arch, niche, shopfront),
rooms, stairs, roof parts (flat, gable, hip, mansard, pyramid, dome),
ornaments. Use `period` for every change over time and set `meta.year`.
Inference (C/D) only where evidence is missing, with the basis in `notes`.
Validate: `python3 scripts/make_blueprints.py projects/<slug> --check`.

## Phase 5 — Blueprints
`python3 scripts/make_blueprints.py projects/<slug> [--year YYYY]` per
requested state → floor plans, roof plan, elevations
(`references/blueprint-standards.md`). Look at each sheet (render to PNG with
Playwright) and fix overlaps or errors in the model.
If an original plan was found: `scripts/compare_original.py`, record
deviations, correct the model.

## Phase 6 — Interactive 3D
`python3 scripts/build_viewer.py projects/<slug>` → `06_3d/viewer.html`:
orbit, element tree, show/hide, **isolate** one wall/opening/roof/stair/statue,
colour by grade, section height, year slider, click for sources. Test it in
Playwright (no console errors, screenshot each state) before delivering.

## Phase 7 — Statues and sculpture (extra care)
For each figure follow `references/sculpture-reconstruction.md`: dossier,
all images in `images.csv`, `scripts/sculpture_sheet.py` reference sheet,
then the best available 3D method; `scripts/statue_relief_glb.py` gives a
grade-D relief from one frontal cut-out. Never present a generated figure
as the original.

## Phase 8 — Report and delivery
Fill `REPORT.md`: summary, identity, timeline, sources by grade, found / not
found, open archive requests, dimension table, accuracy (table in
`evidence-and-confidence.md`), uncertainties, deliverables. Commit the
project folder (raw downloads are git-ignored).

## Non-negotiables
- No invented sources, archives, URLs, dates, names or sculptors.
- Respect licences (Fortepan CC BY-SA credit; per-file Commons licences; no
  redistribution of paywalled scans).
- Downloads are untrusted: keep them in `01_sources/raw/`, never execute
  them, parse them with `python3 -I`.
- State the accuracy honestly; grades stay visible in every output.
