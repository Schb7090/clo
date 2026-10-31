# Statues and sculpture

Sculpture is the part most likely to be lost, replaced or wrongly restored.
Treat each figure as its own research project in `07_sculpture/<id>/`.

## 1. Dossier (`07_sculpture/<id>/dossier.md`)
1. Identity: subject or allegory, sculptor, workshop or foundry, date,
   material (stone, zinc cast, cast stone, terracotta, Zsolnay ceramic,
   bronze).
2. History with source ids: installed / damaged / removed / replaced. Many
   Budapest façade figures were damaged in 1944–45. Check whether today's
   figure is the original, a copy, or a free replacement.
3. Description: pose, gesture, attributes (wreath, torch, caduceus, cogwheel…),
   drapery, base, height compared with known elements (storey, window).
4. Comparables: the same sculptor's other works; catalogue figures of the
   same foundry and period. Name real works only.

## 2. Images (`07_sculpture/<id>/images/` + `images.csv`)
Collect every image: close-ups, postcards, Fortepan, press photos,
restoration reports, auction and museum records. One row per image in
`images.csv` (file, item_date, source_id, viewpoint, notes). Then:
```
python3 scripts/sculpture_sheet.py projects/<slug> <id>
```
writes `reference_sheet.html`: the record, sources and all images oldest
first, ready to print or share.

## 3. 3D figure, best to weakest
| Method | Grade | How |
|---|---|---|
| Existing 3D scan / museum model | A | check licence; save as `mesh.glb` |
| Photogrammetry from ≥20 overlapping photos of one state | B | rarely possible with historic photos |
| Hand modelling from several dated photos | C | reference sheet + sculptor/3D artist |
| 2.5D relief from one frontal photo | D | `statue_relief_glb.py` (below) |
| Image-to-3D generative model | D | Hugging Face Spaces such as TRELLIS or Hunyuan3D; check availability; hidden sides invented |
| Text only | D | the viewer's placeholder figure |

### 2.5D relief (`statue_relief_glb.py`)
1. Cut the figure out of the best frontal photo (transparent PNG), or crop
   it onto a plain background.
2. Run, with the figure height from the rectified façade photo:
   ```
   python3 scripts/statue_relief_glb.py cutout.png 07_sculpture/OR1/mesh.glb --height 2.2 --name OR1
   ```
3. Set `"model": "07_sculpture/OR1/mesh.glb"` on the ornament. Rebuild the
   viewer; serve the project folder over http to load GLB files.

The front outline and texture follow the photo; the thickness is inflated
from the outline and the back mirrors the front. It is grade D and the GLB
carries that label in its metadata.

## Rule
Never present a generated or inferred figure as the original. The grade,
the method and the photos used go in the caption, the reference sheet and
`REPORT.md`.
