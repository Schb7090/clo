# Report — Magyar Állami Operaház, Andrássy út 22., 1061 Budapest

## Summary
The Hungarian State Opera House (Ybl Miklós, 1875–1884) is reconstructed in two states: **as built in 1884**
and **today** (year slider in the 3D model). Ybl's original drawings exist and are online:
the Budapest City Archives' *Ybl Miklós Virtuális Archívum* publishes the Kiscelli Museum's set
(plans of every floor, sections, façades, roof plan). The model is built from those drawings (grade A
for the design), scaled to the OpenStreetMap footprint of the building as it stands (grade B), and
checked against dated photographs from 1883, c.1960 and 1969 (grade B).

Scope: exterior massing of all parts, façade openings, roof parts, main interior volumes (stage,
horseshoe auditorium, grand staircase, vestibule, foyer) and all documented façade sculpture.
Not modelled: interior decoration, box tiers, ornament profiles, building services.

## Deliverables
| What | Where |
|---|---|
| Interactive 3D model (isolate any wall, opening, roof, stair or statue; section cut; year slider; colour by grade; click for sources) | `06_3d/viewer.html` |
| Plans per storey F0–F5, roof plan, four elevations — 1884 and today (22 A3 sheets) | `05_blueprints/*_1884.svg`, `*_2026.svg` |
| Ybl 1879 plan vs reconstruction overlay + deviation table | `05_blueprints/comparison_plan_F0_1884.html` |
| Statue reference sheets (Liszt, Erkel, Melpomene, sphinxes, composer statues) | `07_sculpture/*/reference_sheet.html` |
| Model and its generator (all numbers traceable) | `04_model/building.json`, `04_model/build_model.py` |
| Identity, timeline, dimensions, conflicts | `03_analysis/*.md` |
| Source log (24 sources with grades) | `01_sources/source_log.csv` |

Open the viewer directly (Three.js loads from jsDelivr). In the 3D model, set the section slider to
about +4 m to see the ground-floor interior.

## Identity
See `03_analysis/identity.md`. Royal Hungarian Opera (Magyar Királyi Operaház) until 1945; site on
Hermina tér of the then new Sugárút; architect Ybl Miklós, façade decoration with Schickedanz Albert,
site manager Schmal Henrik; national monument and part of the Andrássy út World Heritage area.

## Timeline (short)
1873 competition → 1874 commission → 1875 permit and start → 1879 revised plans → 1881 composer statues
→ 27 Sep 1884 opening → 1895 electric light → 1912 Medgyaszay alterations → 1939 composer statues
removed → 1944–45 minor war damage, Liszt's head shot off and restored → Dec 1966 new composer statues
→ 1981–84 reconstruction → 2017–2022 full renovation, reopened 12 Mar 2022. Full table: `03_analysis/timeline.md`.

## Sources by grade
- **A — original documents:** Ybl's 1879 ground plan (BTM KM ÉGY 65.048.7), c.1879 main and side
  façades (3261, 3262), roof plan 1879 (76.180), Kozmata longitudinal section, 1875 permit section
  (superseded), Divald's 1883 plates (Rozinay, *Budapest épitményei*, pl. 97, 99), *Bauzeitung für Ungarn* 1880.
- **B — measured / institutional:** OSM footprint; 1883, c.1960 and 1969 archive photographs;
  opera.hu articles on the façade sculpture and the building.
- **C — secondary:** Wikipedia (dimensions infobox), Köztérkép, travel guide (Liszt/Erkel sides), news.

## Found / not found
- Found online: the complete Ybl drawing set (Kiscelli Museum via BFL), contemporary photographs,
  sculpture programme with sculptors.
- Not reachable from this environment: Wikimedia Commons and Wikidata (rate limits), Hungaricana
  (blocks automated clients), Arcanum ADT full text (subscription), Google Street View (not permitted).
- Not found: the parcel number (hrsz.), close-up photos of the 1966 composer statues and of Erkel,
  documentation of the 2017–22 renovation drawings.

## Open archive requests
1. **BTM Kiscelli Múzeum, Építészeti Gyűjtemény** — high-resolution scans (with scale bars legible) of
   BTM KM ÉGY 65.048.2–.7 (floor plans 1879), 3261, 3262 (façades), 76.180 (roof plan),
   51.718.8 (section), 24.229 (half main façade, large scale). Purpose: replace the 2000 px web images
   used here and lift interior dimensions from B to A.
2. **Budapest Főváros Levéltára** — HU BFL XV.17.f.331.b-094 (site plan set) and the *Magyar kir.
   Dalműszínház építési iktatókönyve* 1875–1890; HU BFL XV.17.e.306 file 2242 (Budapesti Műemléki
   Felügyelőség, 1969 survey) for any measured drawings.
3. **MÉM MDK (Tervtár / Fotótár)** — survey drawings of the 1981–84 reconstruction and the 2017–22
   renovation (ZDA – Zoboki Építésziroda); photographs of the 1966 composer statues.
4. **Literature** — Szvoboda Dománszky Gabriella: *Az Operaház – Építészeti séta* (2007); Czétényi
   Piroska: *Az Operaház* (1987); Staud Géza (ed.): *A budapesti operaház 100 éve* (1984).

## Dimensions and accuracy
Key values (full table with methods: `03_analysis/dimensions.md`):

| Element | Value | Grade |
|---|---|---|
| Body length / width / pavilion width | 108.28 / 49.66 / 53.2 m | B |
| Main cornice / balustrade | +21.3 / +23.3 m | B |
| Attic cornice / pavilion roofs | +27.4 / ≈ +30.8 m | B / C |
| High block (auditorium + stage) cornice / roof top / lanterns | +32.8 / +42.2 / ≈ +47 m | B / B / C |
| Stage (inner) | 30.6 × 25.3 m | B |
| Proscenium opening | 14.4 m | B |
| Auditorium ring (outer wall radius) | 15.2 m | B |

Realistic accuracy: plan dimensions ±2–3 % (the 1879 plan and OSM disagree by 2.8 % in length);
heights ±3–5 % (two independent Ybl elevations agree within 2 %); interior positions ±1 m;
statue sizes ±20 %; statue positions along the attic: speculative (D).

## Uncertainties (main ones; all in `03_analysis/conflicts.md`)
- Overall height: 50.69 m (Wikipedia) vs ≈ 47 m to the lantern tips on Ybl's drawings — datum unknown.
- Replacement statues: Dec 1966 (opera.hu) vs 1965 (Wikipedia); Bulgarian vs Süttő limestone.
- Original composer statues: the order on the building is not documented; modelled distribution follows
  the 1883 photograph (13–15 figures visible) with 16 positions (D).
- Melpomene's sculptor: "Brestyánszky Albert" on the 1883 plate vs "Béla" in modern sources.
- Liszt right / Erkel left: single source (C). Thalia/Melpomene sides and Erato/Terpsichore sides: D.
- The stage lantern appears only on the Kozmata section (C); whether both lanterns survive today was
  not verified.
- The curved roofs are approximated by mansard and hip parts; dormers, balustrades, finials omitted.

## Statues — what the pictures show
The closest picture to the originals is the archival photography itself, collected per figure in
`07_sculpture/*/reference_sheet.html`: Liszt (seated abbé, book on lap) and Melpomene (crowned,
dagger) in full-height 1883 close-ups; the 16 original 1881 composer statues on the 1883 attic detail.
The 3D model uses labelled placeholders (grade D). No relief mesh was generated: the niche
backgrounds prevent a clean cut-out, and a mesh made from a guessed outline would misrepresent the
originals. With a cut-out (manual masking or a background-removal tool),
`scripts/statue_relief_glb.py` can produce a grade-D relief for Liszt and Melpomene.
