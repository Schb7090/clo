# Blueprint sheets

The generator produces A3 landscape SVG sheets with a fitted standard scale
(1:50, 1:100, 1:200, 1:500).

Every sheet shows:
- title block: building, address, state/period, sheet title, scale, date,
  "RECONSTRUCTION — NOT A MEASURED SURVEY", evidence legend;
- graphic scale bar (survives reprinting at other sizes);
- plans: north arrow, wall poché, windows (three lines), doors with swing,
  overall and per-wall dimensions, room for annotations;
- elevations: floor lines with levels (±0.00, +4.60 …), openings, ornaments
  as outlined boxes with ids, overall height.

Line colour encodes the evidence grade (A green, B blue, C orange, D red), so
a reader sees at once what is documented and what is guessed.

What the generator does not draw, and you add by hand (edit the SVG or
describe in `REPORT.md`): mouldings profiles, window joinery divisions,
stair geometry, ornament detail. Draw them from rectified photos and mark the
grade next to them.

If an original plan was found, put the scan and the generated plan side by
side (same scale) in `05_blueprints/comparison.html` and list deviations.
