"""Build the catalogue of famous disappearances at sea (data/disappearances.csv).

1. Parse the three Wikipedia lists (parse_lists.py) and add the incidents described in the Bermuda Triangle, Devil's Sea
   (Dragon's Triangle) and Lake Michigan Triangle articles (ARTICLE below, positions read from the article text).
2. Geocode each incident from its location text, in this order:
     Position given      coordinates in the text, or a distance and direction from a named place;
     Near a named place  "off", "near", "around" a cape, island, port or coast in the gazetteer;
     Route midpoint      "between A and B", "from A to B", "en route from A to B": the great-circle midpoint;
     Sea area only       a named sea, gulf or strait (a representative point inside it).
   Whole oceans ("Atlantic Ocean"), land and unknown places are left unplaced. A point that falls on land is moved to the
   nearest sea within 75 km, otherwise left unplaced (routes whose midpoint crosses a continent, for example).
   For the people and aircraft lists, the circumstances text is used only when the location column gives an ocean or
   nothing better.
3. Merge duplicates across the lists (same year and a shared distinctive name word, or the same full date and place),
   keeping the best-placed record.
"""
import collections
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.ops import nearest_points
from common import *
from gazetteer import PLACES, SEAS, OCEANS, LAND
import parse_lists

# ---------- incidents described in the three legend articles (Wikipedia, retrieved 2026) ----------
# (name, kind, year, location text as the article gives it, lon, lat, confidence index, article)
ARTICLE = [
    ("HMS Atalanta", 0, 1880, "sailed from Bermuda for Falmouth, England", None, None, None, "Bermuda Triangle"),
    ("USS Cyclops", 0, 1918, "sailed from Barbados for Baltimore", None, None, None, "Bermuda Triangle"),
    ("Carroll A. Deering", 0, 1921, "found aground and abandoned at Diamond Shoals, near Cape Hatteras", -75.40, 35.15, 1, "Bermuda Triangle"),
    ("SS Cotopaxi", 0, 1925, "wreck found 35 nmi off St. Augustine, Florida", -80.75, 29.85, 0, "Bermuda Triangle"),
    ("USS Proteus", 0, 1941, "lost in the North Atlantic (Caribbean Sea in the list of missing ships)", None, None, None, "Bermuda Triangle"),
    ("USS Nereus", 0, 1941, "lost in the North Atlantic (around the Virgin Islands in the list of missing ships)", None, None, None, "Bermuda Triangle"),
    ("Flight 19", 1, 1945, "training flight east from Fort Lauderdale over the Atlantic", -79.00, 26.60, 1, "Bermuda Triangle"),
    ("PBM Mariner (Flight 19 search)", 1, 1945, "search aircraft, explosion seen by a tanker off the coast of Florida", -80.00, 28.60, 1, "Bermuda Triangle"),
    ("BSAA Star Tiger", 1, 1948, "flight from the Azores to Bermuda", None, None, None, "Bermuda Triangle"),
    ("Airborne Transport DC-3", 1, 1948, "flight from San Juan, Puerto Rico, to Miami", None, None, None, "Bermuda Triangle"),
    ("BSAA Star Ariel", 1, 1949, "flight from Bermuda to Kingston, Jamaica", None, None, None, "Bermuda Triangle"),
    ("Connemara IV", 0, 1955, "yacht found adrift in the Atlantic south of Bermuda", -64.80, 30.50, 1, "Bermuda Triangle"),
    ("KC-135 Stratotankers", 1, 1963, "collided and crashed 300 miles west of Bermuda", -70.40, 32.30, 0, "Bermuda Triangle"),
    ("SS Marine Sulphur Queen", 0, 1963, "Florida Strait (list of missing ships)", None, None, None, "Bermuda Triangle"),
    ("Kaiyo Maru No. 5", 0, 1952, "destroyed by the undersea volcano at Myojin-sho", 140.02, 31.92, 0, "Dragon's Triangle"),
    ("Le Griffon", 0, 1679, "sailed from La Grand Baie (Green Bay) for Lake Erie", -86.90, 45.30, 3, "Michigan Triangle"),
    ("Thomas Hume", 0, 1891, "sailed from Chicago for Muskegon; wreck found in Lake Michigan in 2006", -87.00, 42.60, 2, "Michigan Triangle"),
    ("Rosabelle", 0, 1921, "found capsized in Lake Michigan, crew never found; towed to Racine", -87.40, 42.75, 1, "Michigan Triangle"),
    ("O.M. McFarland (Captain George R. Donner)", 0, 1937, "captain vanished from his cabin approaching Port Washington", -87.65, 43.40, 1, "Michigan Triangle"),
    ("Northwest Orient Airlines Flight 2501", 1, 1950, "debris found 18 miles northwest of Benton Harbor", -86.80, 42.30, 0, "Michigan Triangle"),
    ("Aero L-39 (Schaller and Rodriguez)", 1, 1998, "vanished 27 miles from Cherry Capital Airport, Traverse City", -85.95, 45.15, 1, "Michigan Triangle"),
]

LANDP = [shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]
LTREE = STRtree(LANDP)
GREAT_LAKES = (-92.5, 41.0, -75.5, 49.2)


def on_land(lon, lat):
    if GREAT_LAKES[0] <= lon <= GREAT_LAKES[2] and GREAT_LAKES[1] <= lat <= GREAT_LAKES[3]:
        return False
    p = Point(lon, lat)
    return any(LANDP[i].contains(p) for i in LTREE.query(p))


def to_sea(lon, lat, max_km=75):
    """The point itself if at sea, else the nearest coast point pushed 5 km out to sea, if within max_km; else None."""
    if not on_land(lon, lat):
        return lon, lat
    p = Point(lon, lat)
    best = None
    for i in LTREE.query(p.buffer(1.5)):
        g = LANDP[i]
        if not g.contains(p):
            continue
        q = nearest_points(g.exterior, p)[0]
        best = q
    if best is None:
        return None
    dx, dy = best.x - lon, best.y - lat
    km = math.hypot(dx * math.cos(math.radians(lat)), dy) * 111
    if km > max_km:
        return None
    f = (km + 5) / max(km, .1)
    x, y = lon + dx * f, lat + dy * f
    return (x, y) if not on_land(x, y) else None


# ---------- text matching ----------
def fold(s):
    return (" " + norm(s) + " ").replace(" s ", "s ").strip()


PN0 = sorted(((fold(k), v) for k, v in PLACES.items()), key=lambda kv: -len(kv[0]))
SN = sorted(((fold(k), v) for k, v in SEAS.items()), key=lambda kv: -len(kv[0]))
SEANAMES = {k for k, v in SN}
PN = sorted(PN0 + SN, key=lambda kv: -len(kv[0]))   # places and seas together, so "bermuda triangle" beats "bermuda"


def places_only(ms):
    return [m for m in ms if m[1] not in SEANAMES]


def find_all(text, table):
    """All (start, name, lonlat) matches of gazetteer names in text, longest first, without overlaps."""
    t = " " + fold(text) + " "
    out, used = [], []
    for k, v in table:
        for m in re.finditer(r"(?<= )" + re.escape(k) + r"(?= )", t):
            a, b = m.start(), m.end()
            if any(a < u1 and b > u0 for u0, u1 in used):
                continue
            used.append((a, b)); out.append((a, k, v))
    return sorted(out)


DIRS = {"north": 0, "n": 0, "nne": 22.5, "north-northeast": 22.5, "northeast": 45, "north-east": 45, "ne": 45, "ene": 67.5, "east": 90, "e": 90,
        "ese": 112.5, "southeast": 135, "south-east": 135, "se": 135, "sse": 157.5, "south": 180, "s": 180, "ssw": 202.5, "southwest": 225,
        "south-west": 225, "sw": 225, "wsw": 247.5, "west": 270, "w": 270, "wnw": 292.5, "northwest": 315, "north-west": 315, "nw": 315, "nnw": 337.5}


def coords(text):
    """Coordinates written in the text, as (lon, lat)."""
    m = re.search(r"(-?\d{1,2}\.\d+)\s*;\s*(-?\d{1,3}\.\d+)", text)
    if m:
        return float(m.group(2)), float(m.group(1))
    m = re.search(r"(\d{1,2})°\s*(?:(\d{1,2}(?:\.\d+)?)′\s*)?([NS])\s+(\d{1,3})°\s*(?:(\d{1,2}(?:\.\d+)?)′\s*)?([EW])", text)
    if m:
        lat = int(m.group(1)) + float(m.group(2) or 0) / 60; lon = int(m.group(4)) + float(m.group(5) or 0) / 60
        return (-lon if m.group(6) == "W" else lon), (-lat if m.group(3) == "S" else lat)
    m = re.search(r"(\d{1,3})([EW])\s+(\d{1,2})([NS])", text)
    if m:
        return (-1 if m.group(2) == "W" else 1) * int(m.group(1)), (-1 if m.group(4) == "S" else 1) * int(m.group(3))
    return None


UNIT = r"(nautical miles|nmi|miles|mi|km|kilometers|kilometres)"


def dist_dir(text):
    m = re.search(r"(\d[\d,.]*)\s*" + UNIT + r"(?:\s*\([^)]*\))?\s+(" + "|".join(sorted(DIRS, key=len, reverse=True)) + r")\.?\s+(?:of\s+)?(.*)", text, re.I)
    if not m:
        return None
    km = float(m.group(1).replace(",", "")) * {"nautical miles": 1.852, "nmi": 1.852, "miles": 1.609, "mi": 1.609}.get(m.group(2).lower(), 1)
    pl = places_only(find_all(m.group(4)[:60], PN))
    if not pl:
        return None
    lon, lat = pl[0][2]
    return offset(lon, lat, km, DIRS[m.group(3).lower()]), pl[0][1], km


def route(text):
    """Two gazetteer places joined by between/and, from/to, or 'A to B'."""
    for pat in (r"between (.+?) and (.+)", r"from (.+?) (?:to|for|bound for|towards?) (.+)", r"departed (.+?) for (.+)"):
        m = re.search(pat, text, re.I)
        if not m:
            continue
        a = find_all(m.group(1), PN); b = find_all(m.group(2), PN)
        if a and b:
            return a[-1], b[0]
        return "unresolved"
    return None


def geocode(where, ctx, kind_list):
    """(lon, lat, confidence index, method text) or (None, None, None, reason)."""
    w = where or ""
    for txt, lab in ((w, "location"), (ctx if kind_list != "ships" else "", "circumstances")):
        if not txt:
            continue
        c = coords(txt)
        if c:
            return c[0], c[1], 0, f"coordinates in the {lab} text"
    dd = dist_dir(w)
    if dd:
        (lon, lat), nm, km = dd
        return lon, lat, 0, f"{round(km)} km from {nm}"
    rt = route(w)
    if rt == "unresolved":
        m = re.search(r"(?:off|near|vicinity of|around|close to)\s+(?:the\s+)?(?:coast of\s+)?(.*)", w, re.I)
        pl = places_only(find_all(m.group(1), PN)) if m else []
        if pl:
            return pl[0][2][0], pl[0][2][1], 1, f"near {pl[0][1]}"
        return None, None, None, "route with an end not in the gazetteer"
    if rt:
        (_, an, av), (_, bn, bv) = rt
        lon, lat, km = gc_mid(av[0], av[1], bv[0], bv[1])
        return lon, lat, 2, f"midpoint of {an} to {bn} ({round(km):,} km)"
    pl = places_only(find_all(w, PN))
    if pl:
        # prefer the most specific (last) place inside brackets, else the first named
        inner = re.findall(r"\(([^)]*)\)", w)
        pi = places_only(find_all(" ".join(inner), PN)) if inner else []
        a, nm, (lon, lat) = (pi or pl)[0]
        return lon, lat, 1, f"near {nm}"
    sea = find_all(w, SN)
    if sea and kind_list == "ships" or (sea and not re.search(r"en route|between", ctx or "", re.I)):
        a, nm, (lon, lat) = sea[-1] if "(" in w else sea[0]
        return lon, lat, 3, f"sea area: {nm}"
    f0 = fold(w)
    landish = any(f0 == fold(x) or f0.startswith(fold(x) + " ") for x in LAND)
    if kind_list != "ships" and ctx and not landish:
        dd = dist_dir(ctx)
        if dd:
            (lon, lat), nm, km = dd
            return lon, lat, 0, f"{round(km)} km from {nm} (circumstances text)"
        rt = route(ctx)
        if rt and rt != "unresolved":
            (_, an, av), (_, bn, bv) = rt
            lon, lat, km = gc_mid(av[0], av[1], bv[0], bv[1])
            return lon, lat, 2, f"midpoint of {an} to {bn} ({round(km):,} km, circumstances text)"
        if sea:
            a, nm, (lon, lat) = sea[0]
            return lon, lat, 3, f"sea area: {nm}"
    f = fold(w)
    if not f or any(f == fold(o) or f.startswith(fold(o)) for o in OCEANS):
        return None, None, None, "ocean or unknown only"
    return None, None, None, "on land or not recognised"


# Hand corrections where the automatic reading is wrong (key: list|name|year)
FIX = {
    "ships|USS Gudgeon|1944": (143.53, 22.87, 0, "coordinates in the text (given as W; the list puts it southeast of Iwo Jima, so E)"),
    "ships|Le Griffon|1679": (-86.90, 45.30, 3, "sea area: northern Lake Michigan (lost between Green Bay and the Niagara River)"),
    "ships|SS Hippocampus|1868": (-86.60, 42.20, 1, "near benton harbor"),
    "ships|PS Alpena|1880": (-86.90, 43.10, 3, "sea area: lake michigan"),
    "ships|SS Chicora|1895": (-86.80, 42.60, 3, "sea area: lake michigan (sailed from Milwaukee for St. Joseph)"),
    "ships|SS Bannockburn|1902": (-87.50, 47.60, 3, "sea area: lake superior"),
    "ships|SS D. M. Clemson|1908": (-87.50, 47.60, 3, "sea area: lake superior"),
    "ships|Cerisoles|1918": (-87.50, 47.60, 3, "sea area: lake superior"),
    "ships|Inkerman|1918": (-87.50, 47.60, 3, "sea area: lake superior"),
    "ships|SS R.G. Coburn|1871": (-82.50, 44.80, 3, "sea area: lake huron"),
    "ships|SS Leafield|1913": (-88.90, 48.20, 0, "23 km southeast of port arthur, ontario"),
    "ships|SS James Gayley|1912": (-86.00, 47.60, 1, "northwest of caribou island"),
    "ships|SS Andaste|1929": (-86.40, 42.70, 1, "southwest of holland, michigan"),
    "ships|SS Marquette & Bessemer No. 2|1909": (-80.90, 42.20, 3, "sea area: lake erie"),
    "ships|Java|1869": (None, None, None, "only the destination (Yokohama) is known"),
    "ships|Argo|1814": (None, None, None, "no place given"), "ships|Unity|1813": (None, None, None, "no place given"),
    "ships|HMS Lady Nelson|1825": (125.9, -7.9, 1, "near the Babar islands (Aluta or Baba Island)"),
    "ships|USS Snook|1945": (120.5, 20.5, 2, "between the South China Sea and the Luzon Strait"),
    "ships|U-122|1940": (-4.0, 49.5, 2, "between the North Sea and the Bay of Biscay (English Channel approaches)"),
    "ships|U-240|1944": (4.0, 60.0, 3, "sea area: North Sea west of Norway"),
    "ships|USS Kete|1945": (128.0, 27.0, 1, "near the Ryukyu Islands"),
    "ships|HMS Stonehenge|1944": (93.0, 9.0, 3, "sea area: Bay of Bengal or Andaman Sea"),
    "ships|USS Grayling|1943": (120.2, 15.0, 1, "off Manila or in Lingayen Gulf"),
    "ships|HMS Heureux|1800": (None, None, None, "route too vague (the Caribbean to Halifax)"),
    "ships|København|1928": (None, None, None, "route crosses a whole ocean (Buenos Aires to Australia)"),
    "ships|Burmah|1859": (97.0, -48.0, 0, "last seen near 97E 48S"),
    "ships|Madagascar|1853": (None, None, None, "route spans two oceans (Port Phillip to London)"),
    "ships|Neva|1887": (None, None, None, "route spans two oceans (Banyuwangi to Lisbon)"),
    "ships|Shannon|1885": (None, None, None, "route spans two oceans (London to Calcutta)"),
    "ships|Viscount McDuff|1882": (None, None, None, "route spans an ocean (Sydney to Madras)"),
    "ships|Amy Louise|1909": (None, None, None, "route spans two oceans (Pernambuco to Sydney)"),
    "ships|SS Lord Spencer|1895": (None, None, None, "route rounds a continent (San Francisco to New York)"),
    "ships|SY Aurora|1918": (None, None, None, "route crosses the Pacific (Newcastle to Iquique)"),
    "ships|HMCS Integrity|1805": (None, None, None, "route crosses the Pacific (Sydney to Valparaiso)"),
    "ships|Lyman D. Foster|1919": (None, None, None, "route crosses the Pacific (Nuku'alofa to San Francisco)"),
    "ships|Amelia|1816": (None, None, None, "route too long (Sydney to Java)"),
    "ships|Moy|1905": (None, None, None, "route crosses an ocean (British Guiana to Liverpool)"),
    "ships|Spray|1909": (None, None, None, "route spans the western Atlantic (Vineyard Haven to Venezuela)"),
    "ships|Maratonga|2015": (None, None, None, "route crosses an ocean (Norfolk, Virginia to Portugal)"),
    "ships|Kakanui|1891": (163.5, -50.5, 2, "midpoint of Macquarie Island to southern New Zealand"),
    "ships|USS Porpoise|1854": (None, None, None, "only 'off the coast of China or Taiwan'"),
    "ships|USS Runner|1943": (None, None, None, "only 'off Japan'"),
    "ships|SS Vaitarna|1888": (69.0, 21.0, 1, "off the coast of Saurashtra"),
    "ships|MV Kairali|1979": (69.0, 15.3, 0, "about 500 km off Margao"),
    "ships|Peron|1948": (130.6, -12.2, 1, "near Darwin"),
    "ships|Andrea Gail|1991": (-60.0, 43.9, 1, "off Sable Island"),
    "aircraft|Lockheed Electra 10E (NR 16020)|1937": (-176.6, 0.8, 1, "near Howland Island (Amelia Earhart)"),
    "aircraft|Boeing 777-200ER (9M-MRO)|2014": (None, None, None, "southern Indian Ocean (search area only)"),
    "aircraft|Hawaii Clipper (Martin M-130, NC14714)|1938": (None, None, None, "only 'east of the Philippine coast'"),
    "aircraft|L'Oiseau Blanc (Levasseur PL.8)|1927": (None, None, None, "North Atlantic or Maine"),
    "aircraft|Douglas DC-3 (HS-OOO)|1966": (None, None, None, "only '840 km off the US coast'"),
    "aircraft|Cessna 400 (N636CS)|2025": (-125.5, 30.5, 0, "about 470 miles off San Diego (bearing assumed west-southwest, towards Hawaii)"),
    "aircraft|Light Heart (superpressure balloon)|1974": (-31.5, 28.5, 0, "1610 km west of the Canaries"),
    "aircraft|Free Life (Rozière balloon, N2079)|1970": (-44.0, 41.0, 0, "about 1000 km southeast of Newfoundland"),
    "aircraft|Douglas DC-4 (N3821)|1969": (None, None, None, "route crosses an ocean (Halifax to the Azores)"),
    "aircraft|Rivet Amber (Boeing RC-135)|1969": (179.5, 52.9, 0, "about 400 km east of Shemya"),
    "aircraft|Pathfinder (hydrogen balloon)|1879": (-87.2, 42.6, 3, "sea area: lake michigan"),
    "aircraft|Douglas DC-4|1950": (-86.80, 42.30, 0, "18 miles northwest of Benton Harbor"),
    "aircraft|Cessna 172 (N8342L)|1971": (-86.6, 42.9, 3, "sea area: lake michigan (en route to Holland, Michigan)"),
    "aircraft|Piper Cherokee Arrow (N15206)|1993": (-87.0, 43.8, 3, "sea area: lake michigan (presumed)"),
    "aircraft|Cessna 172 I (N35549)|1993": (-87.0, 43.8, 3, "sea area: lake michigan (presumed)"),
    "aircraft|Aero L-39 Albatross|1998": (-85.95, 45.15, 1, "near Traverse City (Lake Michigan)"),
    "aircraft|F-89C Scorpion (51-5853A)|1953": (-87.5, 47.6, 3, "sea area: lake superior"),
    "aircraft|Piper PA-31-310 Navajo (N174BH)|2012": (-91.4, 46.9, 1, "near two harbors"),
    "aircraft|Beechcraft 80 Queen Air (N242Q)|1980": (None, None, None, "inland lake in Florida"),
    "aircraft|Douglas C-47 (VT-DGS)|1960": (55.3, 25.6, 1, "Persian Gulf near Sharjah"),
    "aircraft|Douglas C-47A|1961": (113.3, -6.9, 1, "near Madura Island"),
    "aircraft|Boeing 307B-1 Stratoliner (F-BELV)|1965": (107.5, 19.5, 1, "Gulf of Tonkin near Hanoi"),
    "aircraft|Antares (Dewoitine D.333, F-ANQA)|1937": (-8.8, 33.5, 1, "near El Jadida"),
    "aircraft|Douglas Dakota (FL650)|1944": (-129.0, 50.5, 1, "off British Columbia"),
    "aircraft|Golden Eagle (NX913)|1927": (-141.7, 30.6, 2, "midpoint of Oakland to Hawaii (Dole Air Race)"),
    "aircraft|Miss Doran (NX2915)|1927": (-141.7, 30.6, 2, "midpoint of Oakland to Hawaii (Dole Air Race)"),
    "aircraft|Dallas Spirit (NX941)|1927": (-141.7, 30.6, 2, "midpoint of Oakland to Hawaii (Dole Air Race search)"),
    "aircraft|Avro Lancastrian (G-AGLX)|1946": (None, None, None, "Indian Ocean only"),
    "aircraft|Douglas C-54A Skymaster (42-107470)|1944": (-38.0, 58.0, 3, "sea area: southeast of Greenland"),
    "aircraft|Örnen (Eagle) (attempted North Pole flight)|1897": (None, None, None, "found on land (Kvitøya) in 1930"),
    "aircraft|Patrie (semi-rigid airship)|1907": (-8.5, 57.5, 1, "off the Hebrides"),
    "aircraft|America (non-rigid airship)|1910": (-70.0, 35.0, 1, "west of Bermuda (abandoned at sea, crew rescued)"),
    "aircraft|Italia (airship)|1928": (25.0, 81.5, 3, "sea area: north of Svalbard (Barents Sea)"),
    "aircraft|Latham 47.02|1928": (18.0, 72.5, 3, "sea area: Barents Sea (near Bear Island)"),
    "aircraft|Hewitt-Sperry Automatic Airplane N-9|1918": (-72.9, 40.4, 1, "south of Long Island"),
    "aircraft|Blériot XI|1913": (-73.6, 40.3, 1, "south of Long Island"),
    "aircraft|Avro 685 York I (OD-ADB)|1958": (None, None, None, "Mediterranean Sea (whole sea, see list)"),
    "aircraft|Commando (Liberator B Mk II (LB-30), AL504)|1945": (-27.0, 39.5, 1, "near the Azores"),
    "aircraft|Lockheed WV-2 Super Constellation (141310)|1958": (-27.5, 38.5, 1, "near the Azores"),
    "people|Vasco de Ataíde|1500": (None, None, None, "Cape Verde or Cape of Good Hope"),
    "people|John Cabot|1499": (None, None, None, "fate unknown (may have reached land)"),
    "people|Harald Kristian Dannevig|1914": (158.9, -54.6, 1, "near Macquarie Island (Endeavour)"),
    "people|Jean-François de Galaup (Lapérouse) and his expedition|1788": (None, None, None, "wrecked at Vanikoro, found in 1826 (not a mystery at sea)"),
    "people|Charles W. Chipp|1881": (130.0, 74.5, 3, "sea area: laptev sea"),
    "people|Eduard von Toll|1902": (149.0, 76.5, 1, "near Bennett Island"),
    "people|Paul Knutsen|1919": (None, None, None, "lost on land, on the Taymyr coast"),
    "people|Peter Tessem|1918": (None, None, None, "lost on land"),
    "people|Clint Castleberry|1944": (-12.0, 5.5, 1, "off Liberia (flight from Roberts Field)"),
    "people|Captain Benjamin Briggs and crew|1872": (-17.5, 38.3, 0, "Mary Celeste found about 400 miles east of the Azores"),
    "people|Arthur Cravan|1918": (None, None, None, "last seen ashore at Salina Cruz"),
    "people|Alan Addis|1980": (None, None, None, "lost on land, East Falkland"),
    "people|Art Scholl|1985": (-117.5, 33.0, 1, "Pacific off southern California"),
    "people|Slim Wintermute|1977": (None, None, None, "inland lake"),
    "people|William B. Ault|1942": (155.5, -15.0, 3, "sea area: Coral Sea (Battle of the Coral Sea)"),
    "people|Samuel Adams|1942": (-177.4, 30.0, 1, "near Midway (Battle of Midway)"),
    "people|Gerhard Köppen|1942": (36.5, 46.0, 3, "sea area: sea of azov"),
    "people|Holly Roth|1964": (-9.35, 32.6, 0, "20 miles north of Safi"),
    "people|Holchu 's 5 crew members|1953": (93.5, 4.0, 0, "about 200 miles south of the Nicobar Islands"),
    "people|Holchu's 5 crew members|1953": (93.5, 4.0, 0, "about 200 miles south of the Nicobar Islands"),
    "people|SS Empire Adur|1955": (112.0, 17.5, 1, "north of the Paracel Islands"),
    "people|Jure Šterk|2009": (None, None, None, "southern Indian Ocean"),
    "people|Experiment|1808": (80.0, -8.5, 0, "coordinates in the circumstances text"),
    "people|Bob Chappell|2009": (147.35, -42.9, 1, "Derwent estuary, Hobart"),
    "people|Tom Lonergan|1998": (147.5, -16.5, 1, "St Crispin Reef, Great Barrier Reef"),
    "people|Daniel Küblböck|2018": (-53.0, 47.5, 3, "sea area: off Newfoundland (Labrador Sea per the list)"),
    "people|Sir Arthur Coningham|1948": (None, None, None, "listed only as 'Bermuda Triangle' (Star Tiger, Azores to Bermuda)"),
}


def main():
    rows = parse_lists.parse()
    for r in rows:
        r["year"] = r["year"] if r["year"] else None
    # article incidents
    for nm, kind, yr, txt, lon, lat, conf, art in ARTICLE:
        rows.append({"list": "article", "kind": kind, "name": nm, "date": str(yr), "year": yr, "where": txt, "context": txt,
                     "section": art, "article": art, "lon0": lon, "lat0": lat, "conf0": conf})
    out = []
    for r in rows:
        key = f"{r['list']}|{r['name']}|{r['year']}"
        if r["list"] == "article" and r.get("lon0") is not None:
            lon, lat, conf, meth = r["lon0"], r["lat0"], r["conf0"], "read from the article text"
        elif key in FIX:
            lon, lat, conf, meth = FIX[key]
        elif r["list"] == "article":
            lon, lat, conf, meth = geocode(r["where"], "", "article")
        else:
            lon, lat, conf, meth = geocode(r["where"], r.get("context", ""), r["list"])
        if conf == 2 and lon is not None:
            mk = re.search(r"\(([\d,]+) km", meth)
            if mk and float(mk.group(1).replace(",", "")) > 7000:
                lon = lat = conf = None; meth = "route too long to place (" + meth + ")"
            elif mk and float(mk.group(1).replace(",", "")) > 4000:
                conf = 3; meth = "long route, counted only in the sea area it crosses: " + meth
        moved = False
        if lon is not None:
            s = to_sea(lon, lat, 200 if conf == 2 else 75)
            if s is None:
                meth = "on land: " + meth; lon = lat = conf = None
            elif (s[0], s[1]) != (lon, lat):
                lon, lat = s; moved = True
        r.update({"lon": None if lon is None else round(lon, 3), "lat": None if lat is None else round(lat, 3), "conf": conf, "method": meth,
                  "moved_to_sea": moved, "key": key})
        out.append(r)
    D = pd.DataFrame(out)
    D["year"] = D.year.astype("Int64")
    print(D.groupby("list").apply(lambda g: pd.Series({"n": len(g), "placed": g.lon.notna().sum()})))
    D.to_json(f"{WORK}/geocoded_rows.json", orient="records", force_ascii=False, indent=1)
    return D


STOP = set("vickers wellington harvard north american martin mariner liberator express commando skymaster dakota "
           "hms uss ss ms mv sy fv rms hmcs ijn ara orp crew of the and sir captain lt ens no airship balloon hydrogen hot air douglas cessna "
           "boeing consolidated lockheed piper avro short catalina pby flight aircraft c 47 mk ii i iii model unknown type registration the a".split())


def tokens(s):
    t = norm(re.sub(r"\(.*?\)", " ", s))
    return {w for w in t.split() if len(w) > 2 and w not in STOP and not w.isdigit()}


MONTHS = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}

# the same incident under names with no word in common (list|name|year -> incident label)
ALIAS = {"aircraft|TBM Avenger (5 planes)|1945": "Flight 19", "article|Flight 19|1945": "Flight 19",
         "aircraft|Douglas DC-3 DST-144 (NC16002)|1948": "DC-3 1948", "article|Airborne Transport DC-3|1948": "DC-3 1948",
         "aircraft|Lockheed Electra 10E (NR 16020)|1937": "Earhart", "people|Amelia Earhart|1937": "Earhart",
         "aircraft|Douglas DC-4|1950": "NW2501", "article|Northwest Orient Airlines Flight 2501|1950": "NW2501",
         "aircraft|Boeing 727 (OB-1303)|1990": "Faucett", "aircraft|Beechcraft 1900 C (ZS-PHL)|2013": "Krause", "people|Jerry Krause|2013": "Krause",
         "aircraft|C-87A Liberator Express (41-24174, c/n 969)|1945": "Harmon", "people|Millard Harmon|1945": "Harmon",
         "aircraft|Douglas C-54A Skymaster (42-107470)|1944": "Vance", "people|Leon Vance|1944": "Vance", "people|1990 Faucett Perú Boeing 727|1990": "Faucett"}


def full_date(s):
    """(year, month, day) when the text gives all three, else None."""
    t = norm(s).split()
    d = [int(x) for x in t if x.isdigit() and len(x) <= 2]; y = [int(x) for x in t if x.isdigit() and len(x) == 4]
    m = [MONTHS[x] for x in t if x in MONTHS]
    return (y[0], m[0], d[0]) if d and y and m else None


def merge(D):
    """Merge duplicate incidents across lists and articles. Rows are joined when they are from the same year and share a
    distinctive name word (for the people list, also a capitalised word of its circumstances text), or are an aircraft
    and a person with the same full date; never two differently named ships or aircraft, never rows with different full
    dates, never rows placed more than 1,500 km apart."""
    D = D.reset_index(drop=True).copy()
    D["toks"] = D.name.map(tokens)
    D["fd"] = D.date.map(full_date)
    D["ctoks"] = D.apply(lambda r: tokens(" ".join(re.findall(r"\b[A-Z][a-zA-Z'\-]{2,}(?: [A-Z][a-zA-Z'\-]{2,})*", r.context or ""))) if r.list == "people" else set(), axis=1)
    D["alias"] = D.key.map(ALIAS)
    parent = list(range(len(D)))
    members = {i: {i} for i in range(len(D))}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    def craft(i):
        r = D.loc[i]
        return (r.list, norm(r["name"])) if r.list in ("ships", "aircraft") else None

    def ok(a, b):
        A, B = members[a], members[b]
        ca = {craft(i) for i in A} - {None}; cb = {craft(i) for i in B} - {None}
        for x in ca:
            for y in cb:
                if x[0] == y[0] and x[1] != y[1]:
                    return False
        fa = {D.loc[i, "fd"] for i in A if D.loc[i, "fd"]}; fb = {D.loc[i, "fd"] for i in B if D.loc[i, "fd"]}
        if fa and fb and not (fa & fb):
            return False
        for i in A:
            for j in B:
                if pd.notna(D.loc[i, "lon"]) and pd.notna(D.loc[j, "lon"]):
                    if gc_mid(D.loc[i, "lon"], D.loc[i, "lat"], D.loc[j, "lon"], D.loc[j, "lat"])[2] > 1500:
                        return False
        return True

    def union(i, j, force=False):
        a, b = find(i), find(j)
        if a == b or not (force or ok(a, b)):
            return
        parent[a] = b; members[b] |= members.pop(a)
    for al, g in D[D.alias.notna()].groupby("alias"):
        ix = list(g.index)
        for k in ix[1:]:
            union(ix[0], k, force=True)
    for pas in ("names", "dates"):
        for y, g in D[D.year.notna()].groupby("year"):
            ix = list(g.index)
            for a in range(len(ix)):
                for b in range(a + 1, len(ix)):
                    i, j = ix[a], ix[b]
                    ri, rj = D.loc[i], D.loc[j]
                    if ri.list == rj.list and ri.list != "ships":
                        continue
                    if pas == "names":
                        same = bool(ri.toks & rj.toks) or bool(ri.toks & rj.ctoks) or bool(rj.toks & ri.ctoks)
                        if ri.list == rj.list == "ships" and not (ri.toks and ri.toks == rj.toks):
                            same = False
                    else:
                        same = ({ri.list, rj.list} == {"aircraft", "people"} and ri.fd and ri.fd == rj.fd
                                and pd.notna(ri.lon) and pd.notna(rj.lon))
                    if same:
                        union(i, j)
    D["grp"] = [find(i) for i in range(len(D))]
    LORD = {"article": 0, "ships": 1, "aircraft": 2, "people": 3}
    recs = []
    for g, G in D.groupby("grp"):
        G = G.assign(cs=G.conf.fillna(9), lo=G.list.map(LORD), kd=G.kind)
        best = G.sort_values(["cs", "lo"]).iloc[0]
        nm = G.sort_values(["kd", "lo"]).iloc[0]   # name: ship or aircraft name before a person's name
        pp = G[G.list == "people"]
        label = nm["name"]
        if nm.kind == 1 and len(pp) and norm(pp.iloc[0]["name"]) not in norm(label) and not pp.iloc[0]["name"].startswith("Crew"):
            label = f"{label}, with {pp.iloc[0]['name']}"
        kind = int(G.kind.min())
        lists = sorted(set(G.list), key=LORD.get)
        arts = sorted(set(a for a in G.get("article", pd.Series(dtype=object)).dropna()))
        persons = [p for ps in G.get("persons", pd.Series(dtype=object)).dropna() for p in ps]
        recs.append({"name": label, "kind": kind, "year": int(G.year.dropna().min()) if G.year.notna().any() else None,
                     "lists": lists, "articles": arts, "where": best["where"], "lon": best.lon, "lat": best.lat, "conf": best.conf,
                     "method": best.method, "moved": bool(best.moved_to_sea), "n_rows": len(G), "persons": persons[:8],
                     "names": sorted(set(G.name))})
    M = pd.DataFrame(recs)
    return M


if __name__ == "__main__":
    D = main()
    M = merge(D)
    jsave(json.loads(M.to_json(orient="records", force_ascii=False)), f"{WORK}/incidents.json", indent=1)
    M = M.sort_values(["year", "name"], na_position="last").reset_index(drop=True)
    M.insert(0, "id", [f"D{i + 1:03d}" for i in range(len(M))])
    out = pd.DataFrame({"id": M.id, "name": M.name, "kind": M.kind.map(lambda k: KINDS[k][0]), "year": M.year.astype("Int64"),
                        "lat": M.lat, "lon": M.lon, "confidence": M.conf.map(lambda c: CONF[int(c)][0] if c == c and c is not None else "Not placed"),
                        "how_placed": M.method, "moved_to_nearest_sea": M.moved, "location_text": M["where"],
                        "wikipedia_lists": M.lists.map(lambda l: "; ".join({"ships": "List of missing ships", "aircraft": "List of missing aircraft",
                                                                         "people": "List of people who disappeared mysteriously at sea", "article": "legend article"}[x] for x in l)),
                        "legend_article": M.articles.map(lambda a: "; ".join(a)), "people_named": M.persons.map(lambda p: "; ".join(p))})
    out.to_csv(f"{DATA}/disappearances.csv", index=False)
    print(len(D), "rows ->", len(M), "incidents;", M.lon.notna().sum(), "placed")
    print(M.conf.value_counts(dropna=False))
