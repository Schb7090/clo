# Deriving dimensions

## Footprint
1. OSM polygon from `footprint_osm.json` (already in local metres).
2. Cross-check against a cadastral or historic map (MAPIRE / city map) for
   the target period: buildings were extended, courtyards built over.
3. Simplify to wall centre lines. Facade walls of 18th–19th c. masonry are
   often 0.6–1.0 m thick at ground floor and thinner upward: record per floor.

## Rectifying a façade photo
1. Pick a photo with the façade as frontal as possible.
2. Mark four points on one plane (e.g. corners of the façade or a window
   grid). Use a homography (OpenCV `getPerspectiveTransform`, or
   `skimage.transform.ProjectiveTransform`) to map them to a rectangle of the
   known footprint width.
3. Scale = known width / pixel width. Read storey heights, sill and lintel
   heights, window widths, cornice heights.
4. Check with a second reference length (door ≈ 2.0–2.4 m, brick course,
   a person ≈ 1.7 m — weak). Record the residual.

Install on demand: `pip install opencv-python-headless numpy`.

## Heights
- OSM `height` / `building:levels` (grade C unless sourced).
- Shadow length with the photo's date and time (grade C).
- Typical storey heights for the type and period (grade C/D), e.g. tall
  representative floors (*piano nobile*) on palaces and tenement houses.

## Roof
- Pitch from an oblique or side photo, or from historic aerial images.
- Ridge direction from the footprint and roof photos.

## Window grid
Count bays per façade in the clearest photo; spacing = façade length / bays
adjusted to the axes. Symmetry is evidence only when a photo confirms it.
