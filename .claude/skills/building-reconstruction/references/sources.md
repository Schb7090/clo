# Budapest source catalogue

Work top to bottom. `fetch_open_data.py` writes `01_sources/search_plan.md`
with ready queries for this list. "Verify" marks an access path that was not
confirmed when this file was written (blocked from the build environment or
unclear coverage): check it, then fix this file.

## Budapest facts that change how you search
- **Budapest exists since 1873** (Pest + Buda + Óbuda). Older records sit
  under the separate towns: Pest, Buda, Óbuda.
- **Street names changed many times** (1870s, 1890s, 1919, 1940s, 1950s,
  1990s). Find every former name of the street first and repeat each
  street-based search with each name, in Hungarian and, before 1918, German.
- **House numbers changed too.** Early 19th c. sources may use conscription
  numbers instead of street numbers (verify per period). Track the parcel
  number (helyrajzi szám, hrsz.): it is the stable key in BFL.
- **Postal code → district**: 1XXY, XX = district (1061 → VI. kerület).
- **Protection levels**: national monument (műemlék), capital local
  protection (fővárosi helyi védelem), district local protection (kerületi
  helyi védelem). Each level has its own documentation.
- **1944–45 siege** damaged many façades, roofs and statues; post-war repairs
  often simplified ornament. Date every photo before trusting it.

## Primary: plans and permits
| Source | Holds | Access | Notes |
|---|---|---|---|
| Budapest Főváros Levéltára (BFL), Tervtár | building permit plans, searchable by hrsz. and address; series XV.17.d.329 (verify) | Hungaricana `archives.hungaricana.hu` (partial); research room; scan order | grade A when found; order scans for the rest |
| BFL, Pest Szépészeti Bizottság (1808–1873) | plans of Pest buildings before unification | BFL (verify digitisation) | German and Hungarian |
| BFL, Buda / Óbuda town records | pre-1873 building matters | BFL | |
| MÉM MDK (Magyar Építészeti Múzeum és Műemlékvédelmi Dokumentációs Központ) | Tervtár (plans), Fotótár (photos), survey drawings of protected buildings | research request | often measured surveys: grade A/B |
| District building authority | post-war permits, alterations | owner or legitimate interest | ÉTDR (`e-epites.hu`) covers only recent electronic permits |
| Land registry (ingatlan-nyilvántartás) | current hrsz., owner | paid (e-hiteles tulajdoni lap / TAKARNET) | use only to get the hrsz. |

## Text: newspapers, journals, books
| Source | Holds | Access | Notes |
|---|---|---|---|
| Arcanum ADT (`adt.arcanum.com`) | full text of Hungarian press 18th c.–today: *Építő Ipar*, *Magyar Építőművészet*, *Vasárnapi Ujság*, *Pesti Napló*, *Budapesti Hírlap*… | search public; full text needs subscription | ask the user to export pages; never claim unread text |
| Hungaricana library (`library.hungaricana.hu`) | journals, Budapest address books (*Budapesti Czím- és Lakásjegyzék*), local history | free; blocks some automated clients | owners and residents per year |
| FSZEK Budapest Gyűjtemény | Budapest local history library, postcards, prints | in person; parts on Hungaricana; image archive (verify URL) | |
| Budapest100 (`budapest100.hu`) | house histories written for the yearly open-house festival | free | secondary, grade C; follow its sources |
| PestBuda (`pestbuda.hu`) | articles on Budapest buildings and streets | free | secondary, grade C |

## Images
| Source | Holds | Access | Notes |
|---|---|---|---|
| Fortepan (`fortepan.hu`) | historic photos, 1900s–1990s, strong Budapest coverage | free search | CC BY-SA 3.0; credit "Fortepan / <donor>" |
| Egykor.hu | old photos by place, often by address | free | user-contributed; licence per image |
| Wikimedia Commons | geotagged photos, postcards | API (`fetch_open_data.py`) | licence per file |
| Köztérkép (`kozterkep.hu`) | public art incl. some façade sculpture, sculptor names | free | verify coverage of façade figures |
| Mapillary | recent street-level photos | needs the user's token | |
| Google Street View | recent street-level photos, several dates | manual look only (no download) | record the imagery date |
| Aerial photos | roofs, courtyards, wings | Hadtörténeti Intézet és Múzeum Térképtár; Arcanum (verify which sets) | |

## Maps
| Source | Holds | Access | Notes |
|---|---|---|---|
| Arcanum Maps / MAPIRE (`maps.arcanum.com`) | georeferenced Habsburg surveys, Budapest city and cadastral maps | viewer; some layers paid | footprint, courtyard and wings per period |
| Hungaricana maps (`maps.hungaricana.hu`) | BFL map collection incl. parcel maps | free (verify) | match hrsz. to plot |
| OpenStreetMap | current footprint, tags | `fetch_open_data.py` | footprint grade B |

## Identity
| Source | Holds | Notes |
|---|---|---|
| Wikidata | architect (P84), inception (P571), heritage (P1435), image (P18), Commons category (P373) | `fetch_open_data.py`; sparse for ordinary houses |
| Műemlékem.hu | monument descriptions, photos | secondary, grade C |
| Monument register | protection status, ID | find the current official register; verify host |

## Not reachable
- Google Maps / Earth / Street View content: no scraping, no tile download.
- Paywalled full text and archive scans that the user did not supply.
- Private interiors: only published photos or the user's own.
