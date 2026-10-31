#!/usr/bin/env python3
"""Geocode the project address and pull open data around it.

Usage: fetch_open_data.py projects/<slug> [--radius 150]

Writes into the project:
  01_sources/geocode.json         Nominatim result
  01_sources/osm_building.json    OSM element(s) at the address with all tags
  01_sources/commons_nearby.json  geotagged Wikimedia Commons files nearby
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
import urllib.parse
import urllib.request
from pathlib import Path

UA = "building-reconstruction-skill/1.0 (historic building research)"
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]


def get_json(url, data=None, timeout=40):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_request(project):
    text = (project / "00_intake/request.md").read_text(encoding="utf-8")
    field = lambda k: re.search(rf"- {k}: (.*)", text).group(1).strip()
    country = field("Country")
    return field("Address"), field("Postal code"), "" if country.startswith("(") else country


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


def geocode(address, postal, country):
    q = {"q": f"{address}, {postal}" + (f", {country}" if country else ""),
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
    out = []
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        val = lambda k: re.sub(r"<[^>]+>", "", md.get(k, {}).get("value", ""))
        out.append({"title": p.get("title"), "page": ii.get("descriptionurl"), "thumb": ii.get("thumburl"),
                    "date": val("DateTimeOriginal"), "license": val("LicenseShortName"),
                    "artist": val("Artist"), "description": val("ImageDescription")[:300]})
    return url, sorted(out, key=lambda r: r["date"] or "9999")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--radius", type=int, default=150)
    args = ap.parse_args()
    project = Path(args.project)
    address, postal, country = parse_request(project)
    src = project / "01_sources"

    try:
        url, hits = geocode(address, postal, country)
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

    try:
        ep, data = overpass_building(lat, lon)
        el = pick_building(data.get("elements", []), best.get("osm_type"), best.get("osm_id"), lat, lon)
        if el is None:
            print("Overpass: no building polygon within 25 m.")
        else:
            (src / "osm_building.json").write_text(json.dumps(el, indent=2, ensure_ascii=False), encoding="utf-8")
            pts = el.get("geometry") or []
            if not pts and el.get("members"):
                outer = [m for m in el["members"] if m.get("role") == "outer"]
                pts = [g for m in outer for g in m.get("geometry", [])]
            poly = [to_local(lat, lon, p["lat"], p["lon"]) for p in pts]
            (project / "04_model/footprint_osm.json").write_text(
                json.dumps({"origin": [lat, lon], "polygon": poly, "tags": el.get("tags", {})}, indent=2,
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

    print("\nNext: manual sweep per references/sources.md (Fortepan, Hungaricana, Arcanum, archives).")


if __name__ == "__main__":
    main()
