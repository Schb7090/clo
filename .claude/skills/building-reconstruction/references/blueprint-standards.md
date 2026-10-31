# Blueprint sheets

`make_blueprints.py` produces A3 landscape SVG sheets at a fitted standard
scale (1:20 … 1:2000):
- `plan_<floor>.svg` — exterior walls (filled), partitions (outlined),
  windows (three lines), doors and gates with swing, shopfronts, niches,
  rooms with name and area, stairs with treads and UP arrow, ornaments at
  that level, overall dimensions, wall lengths, north arrow;
- `plan_roof.svg` — every roof part with ridges and hips, eaves and top
  levels, dashed exterior wall lines;
- `elevation_<facade>.svg` — the façade's walls across all floors, openings,
  ornaments with ids, roof silhouettes from all roof parts (painter-sorted),
  floor levels (±0.00, +4.60 …), overall width.

Every sheet has a title block (name, address, district, hrsz., state/year,
built, architect), scale, date, evidence legend, graphic scale bar, and
"RECONSTRUCTION — NOT A MEASURED SURVEY". Line colour = evidence grade.

Several states: `--year 1900` and `--year 1960` write separate sets
(`plan_F0_1900.svg` …). Without `--year`, `meta.year` is used; if it is
unset, all elements are drawn.

Not generated (add by hand in the SVG or describe in `REPORT.md`, with
grades): moulding profiles, window joinery divisions beyond the basic cross,
ornament detail, sections.

## Comparing with an original plan
When a BFL or MÉM MDK plan is found:
```
python3 scripts/compare_original.py projects/<slug> scan.jpg projects/<slug>/05_blueprints/plan_F0_1900.svg
```
On the page, click two matching points on the scan and on the sheet (e.g.
two street corners of the building); the scan is fitted (scale, rotation,
offset) and overlaid with an opacity slider. Record each difference in
`05_blueprints/deviations.csv` (element, original, reconstruction,
difference, note) and rerun to show the table. Then correct
`building.json`: the original plan is grade A for the design, but the
building as built may differ. Photos decide for the built state.
