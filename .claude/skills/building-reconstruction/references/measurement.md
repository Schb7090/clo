# Deriving dimensions

## Footprint
1. `seed_model.py` turns the OSM polygon (`footprint_osm.json`) into floors
   and exterior walls. Position grade B; heights and thicknesses C/D.
2. Cross-check against a dated map (MAPIRE, BFL parcel maps) for the target
   year: courtyards were built over, wings added, corners cut. Record changes
   in `timeline.md` and use `period` on the affected walls.
3. Budapest masonry walls of the 19th c. are often 0.6–1.0 m thick at the
   ground floor and thinner upward (grade C unless a plan says otherwise).

## Rectifying a façade photo (`rectify_photo.py`)
1. Pick the most frontal photo of the façade for the target period.
2. Open `assets/pick_points.html` in a browser, load the photo, and click
   four points of a rectangle in the façade plane: top-left, top-right,
   bottom-right, bottom-left. Good rectangles: the façade corners at ground
   and cornice level, or the outer edges of a window grid. Then click pairs
   of points to measure. The page writes the command line.
3. Give the rectangle's real size: width from the footprint (grade B), height
   from a plan or a known level. Run:
   ```
   python3 scripts/rectify_photo.py photo.jpg 02_images/rect_S_1905.png \
     --points "TLx,TLy TRx,TRy BRx,BRy BLx,BLy" --width 24.0 --height 12.6 \
     --extend 0.5,0.5,4,0.3 --measure "win:x,y:x,y" --check "x,y:x,y:2.20"
   ```
4. Read storey lines, sill and lintel heights, window widths and cornice
   heights on the gridded output (1 m grid). Record each value in
   `dimensions.md` with method "rectified photo <file>", grade B.
5. Always run at least one `--check` against a second known length (door
   width, a storey height from a plan). Write the residual next to the values.
   Above ±3 %, re-pick the points or use another photo.

Only points in the façade plane measure correctly. Balconies, cornices and
statues project forward: measure their widths, not their depths.

## Heights without a rectangle of known height
- Count courses or use a known door/gate height as the vertical reference.
- OSM `height` / `building:levels` (grade C; OSM height may include towers).
- Typical Budapest storey heights (grade C/D): tall ground floor with shops
  or mezzanine, representative first floor (piano nobile), lower top floors.

## Roof
- Pitch and break height from oblique photos, aerials and the side
  elevations of neighbours; ridge direction from footprint and aerials.
- Split complex roofs into rectangular parts (see `building-schema.md`).

## Window grid
Count bays per façade on the clearest photo; take spacing from the rectified
image, not from symmetry. Symmetry is evidence only where a photo shows it.

## Interior
Only from plans, published interior photos, or the user's own survey. Mark
everything else C/D. Stair position often shows on façades (shifted windows
on the courtyard side) and on old permit plans.
