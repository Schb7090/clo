# Source catalogue

Work top to bottom. Columns: what it holds, how to reach it, limits.
"Verify" means the access path was not confirmed when this file was written:
check it before relying on it, and fix this file if it changed.

## 1. Open data (every country — automated by `fetch_open_data.py`)

| Source | Holds | Access | Limits |
|---|---|---|---|
| OpenStreetMap / Nominatim | geocode, address | `nominatim.openstreetmap.org/search` | 1 req/s, needs User-Agent |
| OpenStreetMap / Overpass | footprint polygon, `building:levels`, `height`, `roof:shape`, `start_date`, `architect`, `heritage`, `wikidata` | `overpass-api.de` and mirrors | tags are volunteer data: grade B for footprint, C for tags |
| Wikimedia Commons | geotagged photos, old postcards, plans | MediaWiki API `list=geosearch` | needs User-Agent; check each file's licence |
| Wikidata | identity, architect, dates, heritage IDs | `query.wikidata.org` SPARQL | sparse for ordinary buildings |
| Mapillary | street-level photos | API needs a free token | ask the user for a token |

## 2. Hungary

| Source | Holds | Access | Limits |
|---|---|---|---|
| Hungaricana (`hungaricana.hu`) | free portal of Hungarian public collections: library (journals, address books), archives, maps, images. Budapest Főváros Levéltára (BFL) building plans (Tervtár) where digitised | web search; `library.`, `archives.`, `maps.` subdomains | blocks some automated clients; coverage of plans is partial |
| BFL — Budapest Főváros Levéltára | building permit plans of Budapest, searchable by parcel (hrsz.) and address | Hungaricana or in person / scan order | not all fonds digitised; order scans for the rest |
| MNL — Magyar Nemzeti Levéltár, county archives | permit plans outside Budapest, estate maps, manorial records | in person, scan order; some on Hungaricana | slow; write a precise request |
| Local building authority (építéshatóság) | later permits, alterations | request by owner or with legitimate interest | ÉTDR covers only recent electronic permits |
| MÉM MDK (Magyar Építészeti Múzeum és Műemlékvédelmi Dokumentációs Központ) | monument documentation: Tervtár (plans), Fotótár (photos), survey drawings | research request | protected buildings mainly |
| Fortepan (`fortepan.hu`) | ~200k+ historic photos, 1900s–1990s, mostly Hungary, searchable by place | web search | CC BY-SA 3.0; credit "Fortepan / <donor>" |
| Arcanum ADT (`adt.arcanum.com`) | full-text Hungarian journals and newspapers 18th c.–today, incl. *Építő Ipar*, *Magyar Építőművészet*, *Vasárnapi Ujság* | search page public; full text needs subscription | ask the user to export pages; do not claim unread content |
| Arcanum Maps / MAPIRE (`maps.arcanum.com`) | georeferenced Habsburg military surveys, cadastral maps, historic city maps | web viewer | viewing free in part, some layers paid |
| Egykor.hu | old photos of Hungarian places, often by address | web | user-contributed, licences vary |
| Műemlékem.hu | descriptions of Hungarian monuments, photos | web | secondary source, grade C |
| FSZEK Budapest Gyűjtemény | Budapest photos, postcards, prints | via Hungaricana (verify) | |
| Budapest address books (*Budapesti Czím- és Lakásjegyzék*) | owners, residents by year | Hungaricana library / ADT (verify which) | |

Search terms to combine: street + number, old street name, `hrsz.`,
`bérház`, `kastély`, `kúria`, `palota`, `villa`, architect name, owner name,
`építési engedély`, `tervrajz`, `homlokzat`, `szobor`, `szoborcsoport`,
German forms (`Zinshaus`, `Palais`, `Schloss`) for pre-1918 material.

## 3. Other countries (start points)

| Country | Plans / surveys | Photos / journals |
|---|---|---|
| Austria | Wiener Stadt- und Landesarchiv (WStLA), Baupolizei files by district | ANNO (Österreichische Nationalbibliothek) newspapers, Bildarchiv Austria |
| Germany | municipal Bauaktenarchiv / Bauordnungsamt; Landesamt für Denkmalpflege | Deutsche Digitale Bibliothek, Deutsche Fotothek |
| UK | Historic England Archive; county record offices | Britain from Above, British Newspaper Archive (paid) |
| France | Archives départementales, Archives de Paris (permis de construire) | Gallica (BnF), Mérimée/POP heritage database |
| USA | HABS/HAER/HALS measured drawings (Library of Congress) — often real measured plans | Library of Congress Prints & Photographs, Chronicling America |
| Czechia / Slovakia | municipal and regional archives, Národní památkový ústav | Kramerius digital libraries |
| Europe-wide | — | Europeana |

If a country is not listed: find (1) the national heritage register,
(2) the archive that holds municipal building permits, (3) the national
digital library, (4) the main open photo archive. Log how you found them.

## 4. Things that are not reachable

- Google Maps / Earth / Street View content: no scraping, no tile download.
  Manual viewing via a browser tool only, recorded as an observation.
- Paywalled full text and archive scans you were not given.
- Private interiors: only published photos or the user's own.
