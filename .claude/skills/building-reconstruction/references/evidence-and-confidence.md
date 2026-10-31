# Evidence grades

Every element in `building.json` and every row in `dimensions.md` gets one grade.

| Grade | Meaning | Typical evidence | Colour |
|---|---|---|---|
| A | Documented | original permit plan, measured survey, HABS drawing, scan | green `#2e7d32` |
| B | Measured | OSM/cadastral footprint, rectified photo with a known reference length, bay counting from a clear photo | blue `#1565c0` |
| C | Inferred | typology of period/region/architect, partial photo, written description | orange `#ef6c00` |
| D | Speculative | no direct evidence; placeholder or illustration (incl. AI image-to-3D) | red `#c62828` |

Rules:
- An element takes the grade of its weakest essential dimension.
- Never upgrade a grade because two weak sources agree; note the agreement.
- A later photo is evidence for the later state only. Date every claim.

# Realistic accuracy

State this table, filled in, in `REPORT.md`.

| Evidence available | Plan dimensions | Heights | Ornament |
|---|---|---|---|
| Original plan scan | ±1–2 % (plan vs as-built may differ) | ±2 % | as drawn |
| Footprint + good rectified photos | ±2–5 % | ±5–10 % | shape only |
| Footprint + few oblique photos | ±5 % | ±10–20 % | approximate |
| Text descriptions only | typological guess | typological guess | illustration |

These ranges are working estimates from photogrammetry practice, not a
standard. Replace them with measured residuals when you have check distances.
