# `building.json` schema

Units: metres. Plan coordinates: `x` east, `y` north, origin anywhere near the
building. `z` up from ground floor level (±0.00). The generators and the
viewer read only this file. See `assets/example_building.json`.

```jsonc
{
  "meta": {
    "name": "string", "address": "string", "postal": "string", "country": "HU",
    "lat": 47.5, "lon": 19.05,           // origin of local coordinates
    "state": "as built 1884",            // which period is modelled
    "architect": "string|null", "built": "1882–1884",
    "disclaimer": "Reconstruction from listed sources; not a measured survey."
  },
  "sources": [ { "id": "S1", "title": "...", "url": "...", "grade": "A" } ],
  "floors": [
    { "id": "F0", "name": "Ground floor", "z": 0.0, "height": 4.6, "slab": 0.35 }
  ],
  "walls": [
    {
      "id": "W1", "name": "Street façade", "floor": "F0",
      "from": [0, 0], "to": [20, 0],     // centre line, plan coords
      "thickness": 0.8,
      "z0": 0.0, "z1": 4.6,              // optional; default floor z..z+height
      "material": "brick, rendered",
      "confidence": "B", "sources": ["S2"], "notes": ""
    }
  ],
  "openings": [
    {
      "id": "O1", "wall": "W1", "type": "window",   // window | door | arch | niche
      "offset": 1.5,                     // from wall.from along the wall to the opening's left edge
      "width": 1.2, "sill": 1.0, "height": 2.4,      // sill relative to wall z0
      "confidence": "B", "sources": ["S2"]
    }
  ],
  "roof": {
    "type": "hip",                       // flat | gable | hip
    "eaves": 9.2, "ridge": 13.0,          // absolute z
    "footprint": [[0,0],[20,0],[20,12],[0,12]],   // gable/hip need 4 points (rectangle)
    "confidence": "C", "sources": ["S3"]
  },
  "ornaments": [
    {
      "id": "R1", "type": "statue",      // statue | relief | cornice | pilaster | balustrade | other
      "name": "Allegory of Commerce", "wall": "W1",
      "position": [10, -0.6, 9.4],       // plan x, y and absolute z of the base centre
      "size": [0.8, 0.6, 2.1],           // width, depth, height
      "sculptor": "string|null", "material": "limestone",
      "model": "07_sculpture/R1/mesh.glb",   // optional; relative to the project folder
      "confidence": "C", "sources": ["S4"], "notes": "pose from 1910 postcard"
    }
  ]
}
```

Checks run by `make_blueprints.py --check`:
- unique ids; every `wall.floor`, `opening.wall` and source id exists;
- grades are A–D;
- openings fit inside their wall (offset + width ≤ length, sill + height ≤ wall height);
- gable/hip roofs have a 4-point footprint.
