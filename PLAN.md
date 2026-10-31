# Plan: building reconstruction from an address

## Goal
Input: an address and a postal code. Output:
1. A sourced dossier on the building: identity, architect, dates, alterations.
2. The original plans, if an archive has digitised them. Otherwise, the
   exact archive request to order them.
3. Reconstructed blueprints: one plan per floor and one elevation per façade,
   as SVG with scale, dimensions and evidence grades.
4. An interactive HTML 3D model. You can show, hide or isolate each wall,
   opening, roof and statue, cut a section, and colour by evidence grade.
5. A separate dossier for each statue, with the best possible visual
   reconstruction and an honest label.

The workflow is the Claude Code skill in
`.claude/skills/building-reconstruction/`. Start it with an address and
Claude runs the phases below.

## Where the request needs correcting
- **"The original blueprint"**: you get one only if an archive holds and has
  digitised it. In Budapest, BFL has permit plans for many buildings, but
  only part is online through Hungaricana. For the rest, the skill writes
  the scan order. Everything else is a reconstruction, and each sheet says so.
- **Arcanum ADT** needs a subscription. Without one, Claude sees only what
  the public search page shows. If you have access, export the relevant pages
  and give them to Claude.
- **Google Maps / Earth / Street View** cannot be scraped or downloaded
  (terms of service, no API access here). The skill uses OpenStreetMap,
  Wikimedia Commons, Fortepan and Mapillary (with your token) instead. With a
  browser tool, Claude can look at Street View and record what it saw.
- **"As close to reality as possible"**: without an original plan or a
  survey, expect ±2–5 % in plan dimensions and ±5–20 % in heights. Each
  element shows its grade (A documented, B measured, C inferred,
  D speculative), so you can see where the model is solid and where it is not.
- **Statues**: a 3D figure built from one or two old photos is an
  illustration. The hidden sides are invented. The skill labels it grade D
  and never presents it as the original.

## Phases (detail in `SKILL.md`)
| # | Phase | Output | Tooling |
|---|---|---|---|
| 0 | Intake: period, your files and subscriptions, scope | `00_intake/request.md` | `new_project.py` |
| 1 | Locate and identify | geocode, OSM footprint and tags, Commons photo list | `fetch_open_data.py` |
| 2 | Archive and literature sweep | `source_log.csv`, `timeline.md` | WebSearch/WebFetch + `references/sources.md` |
| 3 | Image analysis and measurement | `catalog.csv`, `dimensions.md`, `conflicts.md` | `references/measurement.md` (homography rectification) |
| 4 | Building model | `04_model/building.json` | `references/building-schema.md`, `make_blueprints.py --check` |
| 5 | Blueprints | `05_blueprints/*.svg` | `make_blueprints.py` |
| 6 | Interactive 3D | `06_3d/viewer.html` | `build_viewer.py` (Three.js) |
| 7 | Sculpture | `07_sculpture/<id>/` | `references/sculpture-reconstruction.md` |
| 8 | Report | `REPORT.md` | — |

## Status
Done and tested in this branch:
- Skill instructions, source catalogue (Hungary in detail, other countries
  as starting points), evidence grades, schema, measurement and sculpture
  guides.
- `new_project.py`: creates the project folder and templates.
- `fetch_open_data.py`: Nominatim geocoding, OSM footprint and tags (with
  Overpass mirror fallback), Commons geosearch. Tested on Andrássy út 22,
  1061 Budapest: the footprint and tags came back (architect Ybl Miklós,
  1875–1884). Commons was rate-limited from the test container; the script
  reports this and goes on.
- `make_blueprints.py`: validates the model and draws A3 plans and
  elevations (scale bar, north arrow, dimensions, grade colours, title block).
- `build_viewer.py` + `assets/viewer_template.html`: a single-file 3D
  viewer with an element tree, isolate, hide, section slider, grade colours,
  click-to-inspect with sources, and GLB loading for statue meshes.
- `assets/example_building.json`: a fictional test model.

Next steps, in order of value:
1. Run the skill on your first real address and adjust it to what goes wrong.
2. `rectify_photo.py`: four-point homography that produces a scaled façade
   image and a measurement table (OpenCV).
3. Support non-rectangular roofs (L- and U-shaped wings, mansards, domes):
   split the roof into rectangular parts in the schema.
4. Generate a plan-vs-original comparison page when a scan is found.
5. Statue pipeline: reference sheet, optional image-to-3D (grade D), GLB
   into the viewer.
6. Add interior partitions and stairs to the schema (only when sources exist).

## Open questions for you
1. Which period should the default be: as built, or today?
2. Do you have an Arcanum ADT subscription or a Mapillary token?
3. Mostly Hungarian buildings, or other countries too? This decides how far
   to expand `references/sources.md`.
