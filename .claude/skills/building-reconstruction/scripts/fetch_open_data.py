#!/usr/bin/env python3
"""Geocode the Budapest address and pull open data around it.

Usage: fetch_open_data.py projects/<slug> [--radius 150]

Writes into the project:
  01_sources/geocode.json         Nominatim result
  01_sources/osm_building.json    OSM element at the address with all tags
  01_sources/commons_nearby.json  geotagged Wikimedia Commons files nearby
  01_sources/wikidata_nearby.json Wikidata items within 100 m (architect, inception, heritage, image)
  01_sources/search_plan.md       ready-made queries for the manual Budapest archive sweep
  04_model/footprint_osm.json     footprint in local metres (x east, y north)
and appends a row per source to 01_sources/source_log.csv.
Each step fails soft: a blocked service is reported, the rest still runs.
"""
import argparse
import csv
import datetime
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "building-reconstruction-skill/1.0 (historic building research)"
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]


def get_json(url, data=None, timeout=40, retries=3, headers=None):
    """GET/POST JSON; backs off on HTTP 429/503 (rate limits)."""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After") if e.headers else None
            wait = int(ra) if ra and ra.isdigit() else 5 * 2 ** attempt
            if e.code in (429, 503) and attempt < retries and wait <= 60:
                print(f"  {urllib.parse.urlsplit(url).netloc}: HTTP {e.code}, retrying in {wait} s")
                time.sleep(wait)
                continue
            raise


def parse_request(project):
    text = (project / "00_intake/request.md").read_text(encoding="utf-8")
    field = lambda k: re.search(rf"- {re.escape(k)}: (.*)", text).group(1).strip()
    hrsz = field("Parcel (hrsz.)")
    return field("Address"), field("Postal code"), field("District"), "" if hrsz.startswith("(") else hrsz


def log_source(project, row):
    path = project / "01_sources/source_log.csv"
    with path.open(encoding="utf-8") as f:
        n = sum(1 for _ in f)  # header + rows
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([f"S{n}", row["title"], row["repo"], row["url"], "",
                                row["type"], row.get("license", ""),
                                datetime.date.today().isoformat(), row["grade"], row["used_for"], ""])


def to_local(lat0, lon0, lat, lon):
    k = 111320.0
    return [round((lon - lon0) * k * math.cos(math.radians(lat0)), 3), round((lat - lat0) * k, 3)]


def geocode(address, postal):
    q = {"q": f"{address}, {postal}, Hungary", "countrycodes": "hu",
         "format": "jsonv2", "addressdetails": 1, "extratags": 1, "namedetails": 1, "limit": 3}
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(q)
    return url, get_json(url)


def overpass_building(lat, lon):
    query = f"""[out:json][timeout:30];
(way(around:25,{lat},{lon})["building"];relation(around:25,{lat},{lon})["building"];);
out tags geom;"""
    last = None
    for ep in OVERPASS:
        try:
            return ep, get_json(ep, data=urllib.parse.urlencode({"data": query}).encode())
        except Exception as e:  # try next mirror
            last = e
    raise RuntimeError(f"all Overpass endpoints failed: {last}")


def pick_building(elements, osm_type, osm_id, lat, lon):
    for el in elements:
        if el["type"] == osm_type and el["id"] == osm_id:
            return el
    def dist(el):
        pts = el.get("geometry") or []
        if not pts:
            return 1e9
        cy = sum(p["lat"] for p in pts) / len(pts)
        cx = sum(p["lon"] for p in pts) / len(pts)
        return (cy - lat) ** 2 + (cx - lon) ** 2
    return min(elements, key=dist) if elements else None


def commons_nearby(lat, lon, radius):
    q = {"action": "query", "format": "json", "generator": "geosearch",
         "ggscoord": f"{lat}|{lon}", "ggsradius": radius, "ggsnamespace": 6, "ggslimit": 100,
         "prop": "imageinfo|coordinates", "iiprop": "url|extmetadata", "iiurlwidth": 800}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
    data = get_json(url)
    if "error" in data:
        raise RuntimeError(f"Commons API error: {data['error'].get('info', data['error'])}")
    out = []
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        val = lambda k: re.sub(r"<[^>]+>", "", md.get(k, {}).get("value", ""))
        out.append({"title": p.get("title"), "page": ii.get("descriptionurl"), "thumb": ii.get("thumburl"),
                    "date": val("DateTimeOriginal"), "license": val("LicenseShortName"),
                    "artist": val("Artist"), "description": val("ImageDescription")[:300]})
    return url, sorted(out, key=lambda r: r["date"] or "9999")


def wikidata_nearby(lat, lon, km=0.1):
    q = f"""SELECT ?item ?itemLabel ?itemDescription ?archLabel ?inception ?heritageLabel ?image ?commonsCat ?dist WHERE {{
  SERVICE wikibase:around {{ ?item wdt:P625 ?loc . bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "{km}" . bd:serviceParam wikibase:distance ?dist . }}
  OPTIONAL {{ ?item wdt:P84 ?arch . }} OPTIONAL {{ ?item wdt:P571 ?inception . }}
  OPTIONAL {{ ?item wdt:P1435 ?heritage . }} OPTIONAL {{ ?item wdt:P18 ?image . }} OPTIONAL {{ ?item wdt:P373 ?commonsCat . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "hu,en,de". }}
}} ORDER BY ?dist LIMIT 50"""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    data = get_json(url, headers={"Accept": "application/sparql-results+json"})
    rows = {}
    for b in data["results"]["bindings"]:
        v = {k: x["value"] for k, x in b.items()}
        r = rows.setdefault(v["item"], {"item": v["item"], "label": v.get("itemLabel"), "description": v.get("itemDescription"),
                                        "distance_km": round(float(v.get("dist", 0)), 3), "architects": set(),
                                        "inception": set(), "heritage": set(), "image": v.get("image"),
                                        "commons_category": v.get("commonsCat")})
        for key, field in [("archLabel", "architects"), ("inception", "inception"), ("heritageLabel", "heritage")]:
            if v.get(key):
                r[field].add(v[key][:10] if key == "inception" else v[key])
    out = [{k: sorted(x) if isinstance(x, set) else x for k, x in r.items()} for r in rows.values()]
    return url, out


def search_plan(address, postal, district, hrsz, tags, wd):
    """Markdown checklist of exact queries for the manual sweep (see references/sources.md)."""
    street = re.split(r",", address)[0].strip()
    m = re.match(r"(.+?)\s+(\d+[\w/.-]*)\.?$", street)
    sname, num = (m.group(1), m.group(2)) if m else (street, "")
    names = sorted({x for x in [tags.get("name"), tags.get("old_name"), tags.get("alt_name"), tags.get("loc_name")] +
                    [r["label"] for r in wd if r["distance_km"] < 0.03 and r.get("label")] if x})
    arch = sorted(({tags.get("architect", "")} | {a for r in wd if r["distance_km"] < 0.03 for a in r["architects"]}) - {""})
    q = lambda s: f"`{s}`"
    L = [f"# Search plan — {address} ({postal}, {district})", "",
         "Tick each line, log every hit in source_log.csv. Old street names first: look them up, then repeat the "
         "street-based searches with each old name (and German forms before 1918).", "",
         "## Identity", f"- Names: {', '.join(names) or '(none in OSM/Wikidata)'}",
         f"- Architect(s) from OSM/Wikidata: {', '.join(arch) or '(none)'} — confirm in a primary source",
         f"- Parcel (hrsz.): {hrsz or 'unknown — find it (e-hiteles tulajdoni lap / TAKARNET are paid; BFL and old address books list historic hrsz.)'}",
         f"- Former street names of {q(sname)}: search {q(sname + ' korábbi neve')} and {q(sname + ' utcanév története')}", "",
         "## Archives and plans (original drawings)",
         f"- Hungaricana (archives): {q(f'{sname} {num}')} ; {q(f'hrsz {hrsz}') if hrsz else q(f'{district} hrsz')} — filter to Budapest Főváros Levéltára",
         f"- BFL building plans (Tervtár), reference series XV.17.d.329 (verify): search by hrsz. {hrsz or '(find first)'}; if not digitised, write the scan order in REPORT.md",
         "- Pre-1873 Pest buildings: Pest Szépészeti Bizottság (Verschönerungs-Commission) plans at BFL (verify digitisation)",
         "- Protected building? MÉM MDK Tervtár / Fotótár (research request)", "",
         "## Newspapers, journals, address books (Arcanum ADT; Hungaricana library)",
         f"- {q(f'{sname} {num}')} ; {q(f'{sname} {num}. sz.')} ; {q(f'{sname} {num}. számú ház')}",
         *[f"- {q(f'{a} {sname}')} ; {q(f'{a} bérház')} ; {q(f'{a} építész')}" for a in arch],
         *[f"- {q(n)}" for n in names],
         "- Journals to filter on: Építő Ipar, Magyar Építőművészet, Vasárnapi Ujság, Budapesti Hírlap, Pesti Napló",
         "- Address books (Budapesti Czím- és Lakásjegyzék): owner per year", "",
         "## Photos",
         f"- Fortepan: {q(sname)} and each old street name; also {q(district)} ; credit 'Fortepan / donor'",
         f"- Egykor.hu, PestBuda, Budapest100: {q(f'{sname} {num}')}",
         "- Wikimedia Commons: commons_nearby.json; Commons categories from Wikidata: " +
         (", ".join(sorted({r['commons_category'] for r in wd if r.get('commons_category') and r['distance_km'] < 0.05})) or "(none)"),
         "- Mapillary (needs the user's token) and Street View (manual look only, record imagery date)", "",
         "## Maps",
         "- Arcanum Maps / MAPIRE: Budapest historic city and cadastral maps — footprint, courtyard, wings per period",
         "- Compare the OSM footprint with each dated map; record changes in timeline.md", "",
         "## Sculpture",
         f"- {q(f'{sname} {num} szobor')} ; {q(f'{sname} homlokzati szobor')} ; sculptor name once known; Köztérkép (verify coverage of façade sculpture)",
         ]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--radius", type=int, default=150)
    args = ap.parse_args()
    project = Path(args.project)
    address, postal, district, hrsz = parse_request(project)
    src = project / "01_sources"

    try:
        url, hits = geocode(address, postal)
    except Exception as e:
        raise SystemExit(f"Geocoding failed ({e}). Geocode by hand and set meta.lat/lon.")
    if not hits:
        raise SystemExit("Nominatim found nothing. Try the historical street name or ask the user.")
    (src / "geocode.json").write_text(json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8")
    best = hits[0]
    lat, lon = float(best["lat"]), float(best["lon"])
    log_source(project, {"title": f"Nominatim: {best.get('display_name')}", "repo": "OpenStreetMap",
                         "url": url, "type": "geocode", "license": "ODbL", "grade": "B",
                         "used_for": "location"})
    print(f"Geocoded: {best.get('display_name')}  ({lat}, {lon})")
    if len(hits) > 1:
        print("  Other candidates:", *[h.get("display_name") for h in hits[1:]], sep="\n   ")
    time.sleep(1.1)  # Nominatim usage policy

    model_path = project / "04_model/building.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    model["meta"]["lat"], model["meta"]["lon"] = lat, lon
    model_path.write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")

    # Nominatim already carries name and extratags (architect, start_date, heritage…) — fallback if Overpass fails
    tags = {**(best.get("extratags") or {}), **{k: v for k, v in (best.get("namedetails") or {}).items()}}
    try:
        ep, data = overpass_building(lat, lon)
        el = pick_building(data.get("elements", []), best.get("osm_type"), best.get("osm_id"), lat, lon)
        if el is None:
            print("Overpass: no building polygon within 25 m.")
        else:
            (src / "osm_building.json").write_text(json.dumps(el, indent=2, ensure_ascii=False), encoding="utf-8")
            tags = {**tags, **el.get("tags", {})}
            pts = el.get("geometry") or []
            if not pts and el.get("members"):
                outer = [m for m in el["members"] if m.get("role") == "outer"]
                pts = [g for m in outer for g in m.get("geometry", [])]
            poly = [to_local(lat, lon, p["lat"], p["lon"]) for p in pts]
            osm_url = f"https://www.openstreetmap.org/{el['type']}/{el['id']}"
            (project / "04_model/footprint_osm.json").write_text(
                json.dumps({"origin": [lat, lon], "url": osm_url, "polygon": poly, "tags": el.get("tags", {})}, indent=2,
                           ensure_ascii=False), encoding="utf-8")
            osm_url = f"https://www.openstreetmap.org/{el['type']}/{el['id']}"
            log_source(project, {"title": f"OSM building {el['type']}/{el['id']}", "repo": "OpenStreetMap",
                                 "url": osm_url, "type": "footprint+tags", "license": "ODbL",
                                 "grade": "B", "used_for": "footprint"})
            print(f"OSM building {osm_url}: {len(poly)} vertices; tags:")
            for k, v in sorted(el.get("tags", {}).items()):
                print(f"   {k} = {v}")
    except Exception as e:
        print(f"Overpass step skipped: {e}. Fetch the footprint by hand (openstreetmap.org, export).")

    try:
        url, files = commons_nearby(lat, lon, args.radius)
        (src / "commons_nearby.json").write_text(json.dumps(files, indent=2, ensure_ascii=False), encoding="utf-8")
        log_source(project, {"title": f"Wikimedia Commons geosearch r={args.radius} m ({len(files)} files)",
                             "repo": "Wikimedia Commons", "url": url, "type": "photo list",
                             "license": "per file", "grade": "B", "used_for": "images"})
        print(f"Commons: {len(files)} geotagged files within {args.radius} m.")
    except Exception as e:
        print(f"Commons step skipped: {e}. Search commons.wikimedia.org by hand.")

    wd = []
    try:
        url, wd = wikidata_nearby(lat, lon)
        (src / "wikidata_nearby.json").write_text(json.dumps(wd, indent=2, ensure_ascii=False), encoding="utf-8")
        log_source(project, {"title": f"Wikidata items within 100 m ({len(wd)})", "repo": "Wikidata", "url": url,
                             "type": "identity", "license": "CC0", "grade": "C", "used_for": "identity"})
        print(f"Wikidata: {len(wd)} items within 100 m:")
        for r in wd[:8]:
            print(f"   {r['distance_km'] * 1000:5.0f} m  {r['label']}  {', '.join(r['architects'])}  {', '.join(r['inception'])}")
    except Exception as e:
        print(f"Wikidata step skipped: {e}.")

    (src / "search_plan.md").write_text(search_plan(address, postal, district, hrsz, tags, wd), encoding="utf-8")
    print(f"\nWrote {src / 'search_plan.md'} — work through it next (references/sources.md).")


if __name__ == "__main__":
    main()
