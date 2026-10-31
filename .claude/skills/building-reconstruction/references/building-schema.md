# `building.json` schema (v2)

Units: metres. Plan coordinates: `x` east, `y` north, origin near the
building (the geocoded point when seeded). `z` up from ground floor ±0.00.
`make_blueprints.py`, `build_viewer.py` and `sculpture_sheet.py` read only
this file. Full working example: `assets/example_building.json`.
Validate with `make_blueprints.py <project> --check`.

## Common fields
Every wall, opening, roof part, stair and ornament has:
- `id` — unique across the file
- `confidence` — `A` documented, `B` measured, `C` inferred, `D` speculative
- `sources` — list of source ids (required for A and B)
- `notes` — basis of any inference
- `period` — optional `[from_year, to_year]`, `null` = open. Use it for every
  change: a statue lost in 1944, shopfronts cut in 1952, an added storey.
  The viewer gets a year slider; `make_blueprints.py --year 1900` draws one
  state. `meta.year` is the default state.

```jsonc
{
  "meta": { "name": "", "address": "Példa utca 1., Budapest", "postal": "1061",
            "district": "VI. kerület", "hrsz": "28401", "lat": 47.5, "lon": 19.05,
            "year": 1900, "state": "as built", "architect": null, "built": "1889–1891",
            "disclaimer": "Reconstruction from listed sources; not a measured survey." },
  "sources": [ { "id": "S1", "title": "BFL plan …", "url": "…", "grade": "A" } ],

  "floors": [ { "id": "F0", "name": "Földszint", "z": 0.0, "height": 4.6, "slab": 0.4,
                "outline": [[0,0],[24,0],[24,26],[16,26],[16,14],[0,14]] } ],   // outline: slab shape (needed for L/U plans)

  "walls": [
    { "id": "W0S", "floor": "F0", "from": [0,0], "to": [24,0], "thickness": 0.9,
      "facade": "S", "facade_name": "Street façade",   // walls with the same facade share one elevation sheet
      "z0": 0.0, "z1": 4.6,                             // optional; default = floor z … z+height
      "interior": false,                                // true = partition: drawn thin, no elevation
      "material": "brick, lime render", "confidence": "B", "sources": ["S1"] } ],

  "openings": [
    { "id": "O1", "wall": "W0S", "type": "window",      // window | door | arch | niche | shopfront
      "offset": 1.35, "width": 1.3, "sill": 1.2, "height": 2.6,   // offset from wall.from; sill above wall z0
      "confidence": "B", "sources": ["S1"], "period": [null, 1951] } ],

  "rooms": [ { "id": "R01", "floor": "F0", "name": "Kapualj", "polygon": [[8,0],[16,0],[16,9],[8,9]] } ],

  "stairs": [
    { "id": "ST0", "floor": "F0", "type": "dogleg",     // straight | dogleg (two flights + landing)
      "start": [21.6,15.0], "angle": 90,                // first-flight direction, degrees from east, counter-clockwise
      "width": 1.4, "going": 0.3, "steps": 28,          // rise defaults to the floor height
      "landing": 1.6, "gap": 0.2, "confidence": "C", "sources": [] } ],

  "roofs": [                                            // split L/U/complex roofs into parts
    { "id": "RF1", "type": "mansard", "footprint": [[-0.4,-0.4],[24.4,-0.4],[24.4,14.4],[-0.4,14.4]],
      "eaves": 12.6, "break": 16.0, "break_inset": 1.2, "ridge": 17.4, "upper": "hip" },
    { "id": "RF2", "type": "gable",   "footprint": [4 points], "eaves": 12.6, "ridge": 16.0 },
    { "id": "RF3", "type": "hip",     "footprint": [4 points], "eaves": 12.6, "ridge": 15.0 },
    { "id": "RF4", "type": "pyramid", "footprint": [n points], "eaves": 15.0, "ridge": 19.0 },  // corner tower
    { "id": "RF5", "type": "dome",    "center": [12,5], "radius": 2.4, "eaves": 17.0, "ridge": 20.2 },  // radius or [rx, ry]
    { "id": "RF6", "type": "flat",    "footprint": [n points], "eaves": 12.6 } ],

  "ornaments": [
    { "id": "OR1", "type": "statue",                    // statue | relief | cornice | pilaster | balustrade | other
      "name": "Allegory of Industry", "wall": "W2S",
      "position": [12,-0.2,12.6], "size": [0.8,0.6,2.2],   // plan x, y, base z; width, depth, height
      "sculptor": null, "material": "zinc cast",
      "model": "07_sculpture/OR1/mesh.glb",             // optional GLB, relative to the project folder
      "confidence": "D", "sources": ["S2"], "period": [1891,1944] } ]
}
```

Rules the validator enforces:
- unique ids; every referenced floor, wall and source exists;
- openings fit their wall; opening types and roof types are known;
- gable / hip / mansard need a 4-point rectangle; mansard needs `break`;
  dome needs `center` and `radius`; flat / pyramid need a polygon;
- `period` is `[from, to]`.

The file still accepts the v1 single `"roof": {...}` object.
