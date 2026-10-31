# Plan: Budapest building reconstruction from an address

## Goal
Input: a Budapest address and postal code. Output:
1. A sourced dossier: identity, former addresses and street names, parcel
   number, architect, dates, alterations, protection level.
2. The original plans, if an archive has digitised them (BFL Tervtár,
   MÉM MDK). Otherwise, the exact scan order to send.
3. Reconstructed blueprints for each requested year: floor plans, roof plan
   and elevations as SVG, with scale, dimensions and evidence grades.
4. An interactive HTML 3D model. You can show, hide or isolate each wall,
   opening, roof part, stair and statue, cut a horizontal section, move a
   year slider, and colour by evidence grade.
5. A dossier and reference sheet for each statue, plus the best possible
   3D figure with an honest grade.

The workflow is the Claude Code skill in
`.claude/skills/building-reconstruction/`. Give Claude a Budapest address and
it runs the phases below.

## Where the request needs correcting
- **"The original blueprint"**: only if BFL or MÉM MDK holds it and has put it
  online. Hungaricana carries part of BFL's plans. For the rest, the skill
  writes the scan order. Everything else is a reconstruction, and each sheet
  says so.
- **Arcanum ADT** needs a subscription for full text. Without one, Claude
  uses only what the public search page shows. Export pages if you have
  access.
- **Google Maps / Earth / Street View** cannot be downloaded or scraped.
  Claude can look at Street View with a browser tool and record what it saw.
  OSM, Commons, Fortepan, Egykor and Mapillary (with your token) cover the
  rest.
- **Accuracy**: without an original plan or a survey, expect ±2–5 % in plan
  dimensions and ±5–20 % in heights. A rectified photo checked against a
  second known length shows the real error for that façade.
- **Statues**: a figure built from one photo is an illustration (grade D).
  The front outline is right; the depth and back are invented.

## Phases (detail in `SKILL.md`)
| # | Phase | Output | Tooling |
|---|---|---|---|
| 0 | Intake: years, access, scope | `00_intake/request.md` | `new_project.py` (checks the postal code, derives the district) |
| 1 | Locate, identify, seed | geocode, OSM footprint and tags, Commons, Wikidata, `search_plan.md`, first model | `fetch_open_data.py`, `seed_model.py` |
| 2 | Archive and literature sweep | `source_log.csv`, `identity.md`, `timeline.md` | `search_plan.md`, `references/sources.md` |
| 3 | Images and measurement | `catalog.csv`, rectified façades, `dimensions.md` | `pick_points.html`, `rectify_photo.py` |
| 4 | Model | `building.json` with periods | `references/building-schema.md`, `--check` |
| 5 | Blueprints and comparison | `05_blueprints/*.svg`, `comparison_*.html` | `make_blueprints.py`, `compare_original.py` |
| 6 | Interactive 3D | `06_3d/viewer.html` | `build_viewer.py` |
| 7 | Sculpture | dossier, `reference_sheet.html`, `mesh.glb` | `sculpture_sheet.py`, `statue_relief_glb.py` |
| 8 | Report | `REPORT.md` | — |

## Status: built and tested
| Part | Test |
|---|---|
| `new_project.py`: Budapest-only, postal code → district, hrsz., identity template | 1061 → VI. kerület; 2000 refused |
| `fetch_open_data.py`: geocode, OSM (mirror fallback, Nominatim tags fallback), Commons with back-off, Wikidata within 100 m, `search_plan.md` | Andrássy út 22: footprint, Ybl Miklós, 100 Commons files; Wikidata was under an emergency rate limit at test time, which the script reported and skipped |
| `seed_model.py`: walls from the footprint | Opera: 37 → 28 vertices, 5,145 m² |
| `geometry.py`: shared geometry and validation | used by all generators |
| Roofs: flat, gable, hip, mansard, pyramid, dome; several parts | L-shaped example |
| Interior walls, rooms with areas, straight and dogleg stairs | plans and 3D |
| `period` on every element; `--year`; viewer year slider | 1900 vs 2000 states |
| `rectify_photo.py` + `pick_points.html` | synthetic photo: 1.30 m and 2.60 m recovered, 0.0 % check residual |
| `compare_original.py` | rotated scan aligned: scale 1.251 (true 1.25), rotation −3.9° (true −4°) |
| `sculpture_sheet.py`, `statue_relief_glb.py`, GLB in viewer | textured relief loads and faces the street |

Not built (and why):
- **Sections (vertical cuts) as SVG sheets**: the viewer's section slider
  covers horizontal cuts; vertical section sheets can come next if needed.
- **Automatic Fortepan / Hungaricana / Arcanum search**: none of them has a
  documented public API that this workflow can rely on, and Hungaricana
  blocks automated clients. They stay manual, driven by `search_plan.md`.
- **Automatic photogrammetry of statues**: historic photo sets almost never
  have enough overlapping views.

## Open question
- Do you have an Arcanum ADT subscription or a Mapillary token? Without them
  those two sources stay limited (search snippets only; no Mapillary).
