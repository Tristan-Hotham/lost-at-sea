"""Shared paths and helpers for the lost-at-sea project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw6/lost/wiki_*.json
      English Wikipedia articles as parsed HTML ({title, revid, html}), retrieved 2026, Wikipedia contributors, CC BY-SA 4.0:
      "List of missing ships", "List of missing aircraft", "List of people who disappeared mysteriously at sea",
      "Bermuda Triangle", "Devil's Sea" (the Dragon's Triangle) and "Lake Michigan Triangle".
  /home/claude/newdata/raw6/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz
      World Bank, Global Shipping Traffic Density (all vessels), built by the IMF and World Bank from AIS positions,
      January 2015 to February 2021 (https://datacatalog.worldbank.org/search/dataset/0037580), CC BY 4.0. The file is the
      0.08 degree overview level of the published raster (int32, little endian, 2125 rows from 85N to 85S, 4501 columns
      from 180W to 180E). The overview was made by subsampling single full-resolution pixels, so it is only used summed
      over 2 degree cells and named sea areas.
  /home/claude/studies/world-shipwrecks/data/wrecks.csv
      The cleaned, mapped wrecks of the world-shipwrecks study (same author, 2026): positions from the English Wikipedia
      "List of shipwrecks" pages (CC BY-SA 4.0, built from /home/claude/newdata/raw5/wiki_shipwreck_lists.tsv) and from
      Wikidata (CC0), with year of loss and cause. Only the two global records are used here (see 03_losses.py).
  /home/claude/newdata/raw/geo/ne_50m_land.geojson, ne_50m_admin_0_countries.geojson,
      ne_10m_populated_places_simple.geojson   Natural Earth (public domain).
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW6 = os.environ.get("LOST_RAW6", "/home/claude/newdata/raw6")
WRECKS = os.environ.get("LOST_WRECKS", "/home/claude/studies/world-shipwrecks/data/wrecks.csv")
GEO = os.environ.get("LOST_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("LOST_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("LOSTTMP", "/dev/shm/lost"), "work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "lost-at-sea"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23856868"                  # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/lost-at-sea/"            # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
WB_CREDIT = ("World Bank, Global Shipping Traffic Density (IMF and World Bank, from AIS data, January 2015 to February 2021; "
             "Cerdeiro, Komaromi, Liu and Saeed 2020), CC BY 4.0")

CELL = 2.0            # grid cell size in degrees for the cell analysis

# the three legendary areas (vertices as lon, lat; straight lines in longitude and latitude, as usually drawn)
TRIANGLES = {
    "Bermuda Triangle": {"verts": [(-80.19, 25.76, "Miami"), (-64.78, 32.29, "Bermuda"), (-66.11, 18.47, "San Juan")],
                          "col": "#B3202A"},
    "Dragon's Triangle": {"verts": [(139.77, 35.68, "Tokyo"), (144.79, 13.44, "Guam"), (121.56, 25.04, "Taipei")],
                           "col": "#7A4E9C"},
    "Michigan Triangle": {"verts": [(-86.45, 43.96, "Ludington"), (-87.66, 44.09, "Manitowoc"), (-86.45, 42.12, "Benton Harbor")],
                           "col": "#E07B24"},
}
CONF = [("Position given", "#1F3A5F"), ("Near a named place", "#2F7FB8"), ("Route midpoint", "#C9A227"), ("Sea area only", "#9C8460")]
KINDS = [("Ship or boat", "#1F3A5F"), ("Aircraft", "#B3202A"), ("People lost at sea", "#2A9D8F")]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "x1": return f"{float(v):.1f}"
    raise ValueError(f)


def gc_mid(lon1, lat1, lon2, lat2):
    """Great-circle midpoint and distance (km)."""
    p1, l1, p2, l2 = map(math.radians, (lat1, lon1, lat2, lon2))
    bx = math.cos(p2) * math.cos(l2 - l1); by = math.cos(p2) * math.sin(l2 - l1)
    pm = math.atan2(math.sin(p1) + math.sin(p2), math.sqrt((math.cos(p1) + bx) ** 2 + by ** 2))
    lm = l1 + math.atan2(by, math.cos(p1) + bx)
    d = 2 * 6371 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2))
    return (math.degrees(lm) + 540) % 360 - 180, math.degrees(pm), d


def offset(lon, lat, km, bearing):
    """Point km away on a bearing (degrees) from lon, lat."""
    d = km / 6371; b = math.radians(bearing); p = math.radians(lat); l = math.radians(lon)
    p2 = math.asin(math.sin(p) * math.cos(d) + math.cos(p) * math.sin(d) * math.cos(b))
    l2 = l + math.atan2(math.sin(b) * math.sin(d) * math.cos(p), math.cos(d) - math.sin(p) * math.sin(p2))
    return (math.degrees(l2) + 540) % 360 - 180, math.degrees(p2)


def point_in_poly(x, y, poly):
    inside = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][:2]; x2, y2 = poly[(i + 1) % n][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside
