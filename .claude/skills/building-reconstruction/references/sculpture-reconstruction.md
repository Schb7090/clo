# Statues and sculpture

Sculpture is the part most likely to be lost, replaced or wrongly restored.
Treat each figure as its own research project in `07_sculpture/<id>/`.

## Dossier (`07_sculpture/<id>/dossier.md`)
1. Identity: subject or allegory, sculptor, workshop, date, material
   (stone type, zinc cast, terracotta, Zsolnay ceramic, bronze).
2. History: commissioned / installed / damaged / removed / replaced, with
   source ids. Many 19th c. façade statues were zinc or cast stone and
   replaced after war damage: check whether today's figure is the original.
3. Images: every image with date and viewpoint; best close-up first.
4. Description: pose, gesture, attributes (wreath, caduceus, torch…),
   drapery, base, height relative to known elements (storey, window).
5. Comparables: the same sculptor's other works, catalogue figures from the
   same foundry or period with the same subject. Name them, do not invent them.

## Visual reconstruction, best to weakest
| Method | Grade | Note |
|---|---|---|
| Existing 3D scan / museum model | A | check licence |
| Photogrammetry from many overlapping photos (≥20, same state) | B | rarely possible with historic photos |
| Hand modelling / reference sheet from several dated photos | C | state which photos |
| Image-to-3D model from one photo (e.g. Hugging Face Spaces such as TRELLIS or Hunyuan3D — check current availability) | D | hidden sides are invented; illustration only |
| Text-only description | D | silhouette placeholder |

Output: `reference_sheet.png` (best images annotated), optional `mesh.glb`
(set `ornaments[].model` in `building.json` so the viewer loads it), and a
caption that states the method and grade. Never upgrade a generated figure to
"original".
