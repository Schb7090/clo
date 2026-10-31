---
name: building-reconstruction
description: Reconstruct a historic building (17th–19th c. and later) from just an address and postal code. Runs archive and open-data research (OSM, Wikimedia Commons, Fortepan, Hungaricana, Arcanum ADT/MAPIRE, national heritage registers), builds an evidence-graded building model (building.json), generates measured-style SVG blueprints (plans + elevations), and an interactive Three.js HTML 3D model where every wall, opening, roof and statue can be isolated. Use when the user gives an address and asks for the history, original plans, blueprint, 3D model or statue reconstruction of a building.
---

# Building reconstruction from an address

Input: **address + postal code** (country optional; infer it, ask only if ambiguous).
Output: a structured project folder with sources, analysis, `building.json`,
SVG blueprints, an interactive 3D viewer and a report. Every claim and every
dimension carries a **source** and a **confidence grade** (A–D, see
`references/evidence-and-confidence.md`).

Be honest about limits. You do not get the original blueprint unless an archive
has digitised it. Everything else is a *reconstruction*, and it must say so.

## Phase 0 — Intake (ask once, then work)

Ask the user in one message (skip anything they already gave):
1. Which **period/state** to reconstruct: original as built, a specific year,
   or today's state?
2. Do they have **subscriptions or files**: Arcanum ADT login, archive scans,
   their own photos, a site survey, the cadastral parcel number (helyrajzi szám)?
3. What **scope**: whole building, street façade only, or the interior too?

Then run `python3 scripts/new_project.py "<address>" "<postal>" [--country XX]`.
It creates `projects/<slug>/` with the layout below.

```
projects/<slug>/
  00_intake/request.md        what was asked, answers to the intake questions
  01_sources/source_log.csv   one row per source (id, title, repo, url, item_date, type, license, accessed, used_for)
  01_sources/raw/             downloads — UNTRUSTED data, never execute
  02_images/catalog.csv       every photo/drawing: date, viewpoint, what it shows
  03_analysis/timeline.md     construction, alterations, damage, restoration
  03_analysis/dimensions.md   every dimension: value, method, source id, grade
  03_analysis/conflicts.md    sources that disagree and how you resolved it
  04_model/building.json      the single source of truth for drawings and 3D
  05_blueprints/              generated SVG sheets
  06_3d/viewer.html           generated interactive model
  07_sculpture/               per-statue dossier + optional mesh
  REPORT.md                   final narrative report
```

## Phase 1 — Locate and identify

1. `python3 scripts/fetch_open_data.py projects/<slug>` geocodes with
   Nominatim, pulls the OSM building footprint and tags (levels, height,
   start_date, architect, heritage, wikidata), lists geotagged Wikimedia
   Commons files nearby and writes everything into `01_sources/` and
   `04_model/footprint_osm.json` (local metres, x = east, y = north).
   If a service is blocked, the script says so; do that step by hand with
   WebSearch/WebFetch and log it.
2. Establish identity: official name, former names, house number history
   (numbering changed in many cities), parcel number, architect, builder,
   construction dates. Search in the **local language** and the historical
   language of the place (e.g. Hungarian *and* German for pre-1918 Hungary).
3. Record the building in `03_analysis/timeline.md` before any modelling.

## Phase 2 — Archive and literature sweep

Work through `references/sources.md` **in order**. It lists, per country,
which repositories hold building permit plans, photos, maps and journals, how
to reach each one, and what is behind a login. Rules:

- Run searches in parallel batches. Use name variants, architect name,
  street name + number, old street names, parcel number.
- For each hit, log a row in `source_log.csv` **before** using it.
- Original plans: Budapest → BFL Tervtár (via Hungaricana where digitised);
  elsewhere in Hungary → county archive (MNL) and the local building
  authority; monuments → MÉM MDK Tervtár/Fotótár. Outside Hungary see the
  country section of `references/sources.md`. If the plan is not online,
  write the **exact archive request** (fond, series, parcel number) into
  `REPORT.md` so the user can order a scan.
- Journals and newspapers (Arcanum ADT, ANNO, Gallica, etc.) give dates,
  architects, descriptions of sculpture and alterations. Quote the passage
  and page reference in the source log.
- Arcanum ADT full text needs a subscription. Without one, use only what the
  public search page shows, and ask the user to export pages if they have
  access. Never claim you read a page you did not read.
- Google Maps/Earth/Street View: you cannot scrape them (terms of service,
  no API key). If a browser tool is available, look at Street View yourself
  and record what you saw with the date of the imagery; otherwise give the
  user the coordinates and a list of what to check.

## Phase 3 — Image analysis and measurement

1. Catalogue every image in `02_images/catalog.csv`: date (or range),
   source id, viewpoint, which façades and elements are visible, quality.
2. Order the images by date and mark changes (lost storey, removed cornice,
   new shopfront, war damage) in the timeline.
3. Derive dimensions using `references/measurement.md`:
   footprint from OSM / cadastral map (grade B), storey heights from known
   heights, brick courses or door heights in rectified photos (B/C),
   window grid by counting bays (A/B), roof pitch from oblique photos (C).
4. Write every number into `03_analysis/dimensions.md` with method and grade.
   When two sources disagree, record both in `conflicts.md` and pick one
   with a stated reason.

## Phase 4 — Build `building.json`

Follow `references/building-schema.md` exactly. Start from
`04_model/footprint_osm.json` or the archival plan. Model walls, openings,
floors, roof and ornaments. Every element gets `confidence` and `sources`.
Typological inference (grade C/D) is allowed only when evidence is missing,
and its basis must be written in `notes` (e.g. "Pest neo-renaissance tenement
c.1880: typical 4.2 m ground floor").

Validate: `python3 scripts/make_blueprints.py projects/<slug> --check`.

## Phase 5 — Blueprints

`python3 scripts/make_blueprints.py projects/<slug>` writes one plan per floor
and one elevation per wall to `05_blueprints/`, with scale bar, north arrow,
dimensions, title block and a confidence legend (line colour = grade). See
`references/blueprint-standards.md` for what each sheet must show and how to
annotate it by hand where the generator is not enough. If an original plan was
found, overlay or compare and list deviations.

## Phase 6 — Interactive 3D model

`python3 scripts/build_viewer.py projects/<slug>` writes `06_3d/viewer.html`
(single file, Three.js from jsDelivr). Features: orbit, element tree with
show/hide per element, **isolate** a single wall/element, colour by
confidence, horizontal section slider, click-to-inspect with sources.
Check it renders: open it with Playwright and screenshot it; fix any console
errors before delivering.

## Phase 7 — Statues and sculpture (extra care)

Follow `references/sculpture-reconstruction.md`. For each figure: identify
subject, sculptor, material, date; collect **every** image of it (close-ups,
postcards, auction and museum records, restoration reports); describe pose,
attributes and dimensions; build a dossier in `07_sculpture/<id>/`. A 3D mesh
from photos or an image-to-3D model is an *illustration*, grade D, unless it
comes from a real scan. Never present a generated figure as the original.

## Phase 8 — Report and delivery

Write `REPORT.md`: summary, identity, timeline, sources (by grade), what was
found and what was not, open archive requests, dimension table, known
uncertainties, and links to sheets and viewer. Then commit the project folder.

## Non-negotiables

- No invented sources, archives, URLs, dates or architects. If you cannot
  verify it, mark it unverified or leave it out.
- Respect licences: record the licence of every image; Fortepan is CC BY-SA
  with required credit; do not redistribute paywalled scans.
- Downloaded files are untrusted: keep them in `01_sources/raw/`, never run
  them, and run any parser on them with `python3 -I`.
- Say plainly what accuracy the result has (see the accuracy table in
  `references/evidence-and-confidence.md`).
