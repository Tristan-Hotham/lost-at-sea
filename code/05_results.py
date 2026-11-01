"""Every number used anywhere (data/results.json), the page data (data/points.json, data/losses_points.json,
data/seas.json, data/cells.json, data/site.json) and checks on statements made in words."""
import numpy as np
import pandas as pd
from pyproj import Geod
from shapely.geometry import shape, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union
from common import *
from areas import AREAS, NAMES, REST

AN = jload(f"{WORK}/analysis.json")
D = pd.read_csv(f"{DATA}/disappearances.csv")
P = pd.read_csv(f"{WORK}/placed.csv")
L = pd.read_csv(f"{DATA}/losses.csv")
C = pd.read_csv(f"{DATA}/cells.csv")
LM = jload(f"{WORK}/losses_meta.json")
RAW = jload(f"{WORK}/geocoded_rows.json")
AR = {a["area"]: a for a in AN["areas"]}
pc = lambda a, b: round(100 * a / b, 2) if b else 0.0
geod = Geod(ellps="WGS84")
R = {"meta": {"doi": DOI, "blog": BLOG, "page": PAGE, "repo": REPO, "retrieved": RETRIEVED}}

# ---------------- catalogue ----------------
rows = pd.DataFrame(RAW)
nl = rows.list.value_counts()
conf = D.confidence.value_counts()
kinds = D.kind.value_counts(); pk = P.kind.value_counts()
why = D[D.lat.isna()].how_placed.fillna("")
why_g = {"ocean": int(why.str.contains("ocean or unknown|Ocean only|search area|only '|Indian Ocean only|southern Indian").sum()),
         "land": int(why.str.contains("on land|lost on land|inland|ashore|found on land|not a mystery").sum()),
         "route": int(why.str.contains("route").sum())}
why_g["other"] = int(len(why) - sum(why_g.values()))
R["cat"] = {"rows_ships": int(nl["ships"]), "rows_aircraft": int(nl["aircraft"]), "rows_people": int(nl["people"]), "rows_article": int(nl["article"]),
            "rows": int(len(rows)), "n": len(D), "merged": int(len(rows) - len(D)), "placed": int(D.lat.notna().sum()),
            "placed_pct": pc(D.lat.notna().sum(), len(D)), "unplaced": int(D.lat.isna().sum()), "why": why_g,
            "conf": {c[0]: int(conf.get(c[0], 0)) for c in CONF}, "conf_pct": {c[0]: pc(conf.get(c[0], 0), D.lat.notna().sum()) for c in CONF},
            "kinds": {k[0]: int(kinds.get(k[0], 0)) for k in KINDS}, "placed_kinds": {k[0]: int(pk.get(k[0], 0)) for k in KINDS},
            "placed_aircraft_pct": pc(pk.get("Aircraft", 0), len(P)),
            "year_min": int(P.year.min()), "year_max": int(P.year.max()), "median_year": int(P.year.median()),
            "pre1946_pct": pc((P.year < 1946).sum(), P.year.notna().sum()), "moved": int(D.moved_to_nearest_sea.sum()),
            "placed_cells": AN["n"]["placed_cells"], "placed_1800": AN["n"]["placed_1800"], "placed_1946": AN["n"]["placed_1946"],
            "war_pct": pc((P.year.between(1914, 1918) | P.year.between(1939, 1945)).sum(), len(P))}
import importlib.util as _iu
_sp = _iu.spec_from_file_location("d1", os.path.join(ROOT, "code", "01_disappearances.py")); _m = _iu.module_from_spec(_sp); _sp.loader.exec_module(_m)
from gazetteer import PLACES as _PL, SEAS as _SE
R["cat"]["fixes"] = len(_m.FIX) + len(_m.ARTICLE); R["cat"]["gaz_places"] = len(set(_PL.values())); R["cat"]["gaz_seas"] = len(set(_SE.values()))
dec = P.dropna(subset=["year"]).assign(dec=lambda x: (x.year // 10 * 10).astype(int))
dec = dec[dec.dec >= 1800]
R["cat"]["decades"] = [{"dec": int(d), **{k[0]: int(((dec.dec == d) & (dec.kind == k[0])).sum()) for k in KINDS}} for d in range(1800, 2030, 10)]
pk_dec = max(R["cat"]["decades"], key=lambda r: sum(r[k[0]] for k in KINDS))
R["cat"]["peak_decade"] = pk_dec["dec"]; R["cat"]["peak_decade_n"] = sum(pk_dec[k[0]] for k in KINDS)

# ---------------- losses and traffic ----------------
Ly = L[L.year.between(1800, 2025)]
R["losses"] = {"n": LM["n_kept"], "n_wikipedia": LM["n_wikipedia"], "n_wikidata": LM["n_wikidata"], "n1800": AN["n"]["losses_1800"],
               "n2000": AN["n"]["losses_2000"], "n2015": AN["n"]["losses_2015"],
               "war_pct_1800": pc(Ly.war_year.sum(), len(Ly))}
R["traffic"] = {"cells": AN["n"]["cells_with_traffic"], "lanes_min": jload(f"{WORK}/lanes.json")["min_positions"]}


# ---------------- area tests ----------------
def T(nm, key="T"):
    t = AR[nm][key]
    return {**t, "x": round(t["ratio"], 1) if t and t["ratio"] is not None else None}


R["areas"] = []
for a in AN["areas"]:
    R["areas"].append({"name": a["area"], "short": a["short"], "group": a["group"], "traffic_pct": a["traffic_share_pct"], "lanes_pct": a["lanes_share_pct"],
                       "T": a["T"], "T_lanes": a["T_lanes"], "T_1946": a["T_1946"], "T_ships": a["T_ships"], "T_lists": a["T_lists"], "L": a["L"],
                       "L_peace": a["L_peace"], "M": a["M"], "M_lanes": a["M_lanes"], "losses_1800": a["losses_1800"], "losses_2000": a["losses_2000"],
                       "kinds": a["kinds"], "median_year": a["median_year"]})
A = {a["name"]: a for a in R["areas"]}
hi = [a for a in R["areas"] if a["T"]["flag"] == "higher" and a["name"] != REST]
lo = [a for a in R["areas"] if a["T"]["flag"] == "lower"]
R["natl"] = {"o": A["North Atlantic, open ocean"]["T"]["o"], "e": A["North Atlantic, open ocean"]["T"]["e"]}
R["T"] = {"n_areas": len(AREAS) + 1, "higher": [a["name"] for a in hi], "n_higher": len(hi), "lower": [a["name"] for a in lo], "n_lower": len(lo),
          "higher95": [a["name"] for a in R["areas"] if a["T"]["flag"].startswith("higher")]}

# ---------------- Bermuda Triangle ----------------
def tri_poly(nm):
    return Polygon([(v[0], v[1]) for v in TRIANGLES[nm]["verts"]])


def km_outside(nm, lon, lat):
    """Great-circle distance (km) from a point to the triangle; 0 inside."""
    pg = tri_poly(nm)
    from shapely.geometry import Point
    if pg.contains(Point(lon, lat)):
        return 0.0
    vs = TRIANGLES[nm]["verts"]; best = 1e9
    for i in range(3):
        a, b = vs[i], vs[(i + 1) % 3]
        for t in np.linspace(0, 1, 400):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            best = min(best, geod.inv(lon, lat, x, y)[2] / 1000)
    return best


def tri_area(nm):
    vs = TRIANGLES[nm]["verts"]
    # densify the straight lon/lat edges before measuring
    xs, ys = [], []
    for i in range(3):
        a, b = vs[i], vs[(i + 1) % 3]
        for t in np.linspace(0, 1, 200, endpoint=False):
            xs.append(a[0] + (b[0] - a[0]) * t); ys.append(a[1] + (b[1] - a[1]) * t)
    return abs(geod.polygon_area_perimeter(xs, ys)[0]) / 1e6


famous = {}
for nm in TRIANGLES:
    F = D[D.legend_article.fillna("").str.contains(nm.split("'")[0].split()[0])]
    lst = []
    for f in F.itertuples():
        if f.lat == f.lat:
            d = km_outside(nm, f.lon, f.lat)
            inside = d == 0 and f.confidence != "Sea area only"
            lst.append({"name": f.name, "year": int(f.year), "kind": f.kind, "conf": f.confidence, "km": round(d), "inside": bool(inside),
                        "where": f.location_text, "lat": f.lat, "lon": f.lon, "id": f.id})
        else:
            lst.append({"name": f.name, "year": int(f.year), "kind": f.kind, "conf": "Not placed", "km": None, "inside": False, "where": f.location_text, "id": f.id})
    famous[nm] = {"n": len(lst), "inside": sum(x["inside"] for x in lst), "within300": sum(1 for x in lst if x["km"] is not None and x["km"] <= 300),
                  "list": lst, "area_km2": round(tri_area(nm), -3)}
R["famous"] = famous
NB = AN["neighbours"]
bt = A["Bermuda Triangle"]
R["bermuda"] = {"o": bt["T"]["o"], "e": bt["T"]["e"], "x": bt["T"]["ratio"], "lo": bt["T"]["lo"], "hi": bt["T"]["hi"], "flag": bt["T"]["flag"],
                "p_up": bt["T"]["p_up"], "traffic_pct": bt["traffic_pct"], "lanes_x": bt["T_lanes"]["ratio"], "lanes_flag": bt["T_lanes"]["flag"],
                "o46": bt["T_1946"]["o"], "e46": bt["T_1946"]["e"], "x46": bt["T_1946"]["ratio"], "flag46": bt["T_1946"]["flag"],
                "ships_o": bt["T_ships"]["o"], "ships_x": bt["T_ships"]["ratio"],
                "L_o": bt["L"]["o"], "L_e": bt["L"]["e"], "L_x": bt["L"]["ratio"], "L_lo": bt["L"]["lo"], "L_hi": bt["L"]["hi"], "L_flag": bt["L"]["flag"],
                "Lpeace_x": bt["L_peace"]["ratio"], "Lpeace_flag": bt["L_peace"]["flag"], "losses_1800": bt["losses_1800"],
                "M_o": bt["M"]["o"], "M_e": bt["M"]["e"], "M_x": bt["M"]["ratio"], "M_flag": bt["M"]["flag"],
                "neigh_o": NB["o_neigh"], "neigh_e": NB["neigh_T"]["e"], "neigh_x": NB["neigh_T"]["ratio"], "neigh_lo": NB["neigh_T"]["lo"], "neigh_hi": NB["neigh_T"]["hi"],
                "within_share_pct": round(100 * NB["traffic_share_bermuda_within"], 1), "within_e": NB["expected_bermuda_within"], "within_p": round(NB["p"], 2),
                "within_loss_share_pct": round(100 * NB["loss_share_bermuda_within"], 1), "within18_e": NB["expected18_bermuda_within"],
                "within18_o": NB["o18_bermuda"], "within18_p": round(NB["p_losses"], 3), "neigh_losses": NB["losses_neigh"],
                "area_km2": famous["Bermuda Triangle"]["area_km2"],
                "names": P[P.area == "Bermuda Triangle"].sort_values("year").apply(lambda r: f"{r['name']} ({int(r.year)})", axis=1).tolist(),
                "famous_n": famous["Bermuda Triangle"]["n"], "famous_inside": famous["Bermuda Triangle"]["inside"],
                "famous_within300": famous["Bermuda Triangle"]["within300"]}
B = R["bermuda"]
B["group_n"] = NB["o_bermuda"] + NB["o_neigh"]
inside_names = [x["name"] for x in famous["Bermuda Triangle"]["list"] if x["inside"]]
B["famous_inside_names"] = inside_names
bcell = [r for r in AN["ranked_cells"] if r["area"] == "Bermuda Triangle"]
B["flagged_cells"] = len(bcell)
B["flagged_cell"] = bcell[0] if bcell else None

dt = A["Dragon's Triangle"]
R["dragon"] = {"o": dt["T"]["o"], "e": dt["T"]["e"], "x": dt["T"]["ratio"], "lo": dt["T"]["lo"], "hi": dt["T"]["hi"], "flag": dt["T"]["flag"],
               "traffic_pct": dt["traffic_pct"], "L_x": dt["L"]["ratio"], "L_flag": dt["L"]["flag"], "M_o": dt["M"]["o"], "M_e": dt["M"]["e"],
               "war": int(((P.area == "Dragon's Triangle") & (P.year.between(1939, 1945))).sum()),
               "names": P[P.area == "Dragon's Triangle"].sort_values("year").apply(lambda r: f"{r['name']} ({int(r.year)})", axis=1).tolist(),
               "area_km2": famous["Dragon's Triangle"]["area_km2"]}
mt, ml, gl = A["Michigan Triangle"], A["Rest of Lake Michigan"], A["Rest of the Great Lakes"]
R["michigan"] = {"o": mt["T"]["o"], "e": mt["T"]["e"], "hi": mt["T"]["hi"], "lake_o": ml["T"]["o"], "lake_e": ml["T"]["e"], "lake_x": ml["T"]["ratio"],
                 "lake_lo": ml["T"]["lo"], "lake_hi": ml["T"]["hi"], "lake_L_x": ml["L"]["ratio"], "lake_lanes_x": ml["T_lanes"]["ratio"],
                 "gl_o": gl["T"]["o"], "gl_e": gl["T"]["e"], "gl_x": gl["T"]["ratio"], "gl_L_x": gl["L"]["ratio"],
                 "lake_pre1946": int(((P.area.isin(["Rest of Lake Michigan", "Michigan Triangle"])) & (P.year < 1946)).sum()),
                 "sea_only_in_triangle": int(((P.confidence == "Sea area only") & P.apply(lambda r: tri_poly("Michigan Triangle").contains(__import__("shapely.geometry", fromlist=["Point"]).Point(r.lon, r.lat)), axis=1)).sum()),
                 "famous_n": famous["Michigan Triangle"]["n"], "famous_inside": famous["Michigan Triangle"]["inside"],
                 "famous_within50": sum(1 for x in famous["Michigan Triangle"]["list"] if x["km"] is not None and x["km"] <= 50),
                 "area_km2": famous["Michigan Triangle"]["area_km2"]}

# ---------------- the places that really are worse ----------------
EXPL = {  # area -> (causes, short explanation)
    "Bass Strait and Tasman Sea": ("weather, shoals, reporting", "Colonial-era coastal traders lost between Sydney, Hobart, Launceston and Port Phillip, in a strait swept by westerly gales and strewn with islands and reefs; one section of the Wikipedia list carefully gathers these Australian losses, and receivers pick up relatively little AIS traffic here today."),
    "Rest of Lake Michigan": ("weather, history, reporting", "Nineteenth- and early twentieth-century lake freighters and schooners caught by sudden autumn gales on a long, open lake, when lake traffic was far busier than it is today; the losses are richly documented by American newspapers and enthusiasts."),
    "Rest of the Great Lakes": ("weather, history", "Lake Superior and Lake Huron storms, above all the November gales, which sank freighters that left no trace; busy lake trade a century ago."),
    "US Atlantic coast": ("shoals, weather, reporting", "Cape Hatteras and the Diamond Shoals, Gulf Stream storms, and a long tail of American light aircraft and yachts, reported by an English-language press that Wikipedia draws on heavily."),
    "English Channel": ("war, aviation, reporting", "Pioneer aviators (Walter Powell, Cecil Grace, Gustav Hamel), pilots of the Battle of Britain, and Glenn Miller's aircraft: short flights over water, often in war, all well reported in English."),
    "Newfoundland and the Grand Banks": ("weather, aviation", "Fog, ice and gales at the corner of the North Atlantic, where the great-circle routes to Europe begin: pioneer transatlantic flights of 1927 and 1928 and steamers such as the Arctic were lost here."),
    "Caribbean Sea": ("weather, history", "Hurricanes, and the warships and packets of the 1700s and 1800s (USS Insurgent, USS Albany, HMS Babet), plus light aircraft in recent decades."),
    "Rest of the world's seas": ("aviation", "Mostly long ocean flights: the Dole Air Race of 1927 and the approaches to Hawaii, where few ships go today."),
}
R["worse"] = []
for a in sorted([a for a in R["areas"] if a["T"]["flag"] == "higher" and a["name"] in EXPL], key=lambda a: a["T"]["p_up"]):
    R["worse"].append({"name": a["name"], "o": a["T"]["o"], "e": a["T"]["e"], "x": a["T"]["ratio"], "lo": a["T"]["lo"], "hi": a["T"]["hi"],
                       "lanes_x": a["T_lanes"]["ratio"], "lanes_flag": a["T_lanes"]["flag"], "L_x": a["L"]["ratio"] if a["L"] else None,
                       "L_flag": a["L"]["flag"] if a["L"] else None, "causes": EXPL[a["name"]][0], "why": EXPL[a["name"]][1],
                       "median_year": a["median_year"], "aircraft": a["kinds"]["Aircraft"]})
assert {w["name"] for w in R["worse"]} >= set(R["T"]["higher"]) - {"Michigan Triangle"}, set(R["T"]["higher"])
CELLX = [  # (lat0, lon0) of a cell -> (place, causes)
    ((-41.0, 144.0), "Bass Strait, west (King Island, Port Phillip)", "weather, shoals"), ((-41.0, 146.0), "Bass Strait, Tasmania's north coast", "weather, shoals"),
    ((-39.0, 148.0), "Bass Strait, east (Furneaux and Kent Groups)", "weather, shoals"), ((-35.0, 150.0), "Off Sydney and Botany Bay", "weather, reporting"),
    ((21.0, -158.0), "Hawaii, Oahu and Molokai", "aviation"), ((29.0, -142.0), "Mid-Pacific, Oakland to Hawaii", "aviation (Dole Air Race)"),
    ((41.0, -88.0), "Southern Lake Michigan", "weather, history"), ((45.0, -54.0), "Off Cape Race, Newfoundland", "weather, aviation"),
    ((-45.0, 166.0), "Fiordland, Milford Sound", "aviation"), ((-55.0, 158.0), "Macquarie Island", "weather"),
    ((-45.0, 148.0), "South-east Tasmania", "weather, shoals"), ((-45.0, 146.0), "Hobart and the Derwent", "weather, reporting"),
    ((-41.0, 148.0), "North-east Tasmania", "weather, shoals"), ((-33.0, 154.0), "Tasman Sea off New South Wales", "weather"),
    ((-39.0, 144.0), "Port Phillip Heads", "weather, reporting"), ((27.0, -178.0), "Midway", "war"),
    ((-37.0, 150.0), "Far south coast of New South Wales", "weather, shoals"), ((17.0, -68.0), "Mona Passage and Puerto Rico", "aviation, reporting"),
    ((37.0, -124.0), "Off San Francisco", "aviation, reporting"), ((-23.0, 166.0), "New Caledonia", "war, aviation"),
    ((59.0, -44.0), "Off Cape Farewell, Greenland", "weather, ice"), ((31.0, -80.0), "Off Georgia and South Carolina", "weather, reporting"),
    ((33.0, -120.0), "Off Los Angeles", "aviation, reporting"), ((-9.0, 156.0), "Solomon Islands", "war"), ((25.0, -82.0), "Florida Keys and Straits", "aviation, reporting"),
    ((23.0, -78.0), "Bahamas (inside the Bermuda Triangle)", "aviation"), ((45.0, -88.0), "Green Bay, Lake Michigan", "weather, history"),
    ((39.0, -74.0), "Off New Jersey and Long Island", "aviation, reporting")]
cx = {k: (p, c) for k, p, c in CELLX}
R["cells"] = {"n_flagged": AN["n"]["cells_flagged"], "with_D": AN["n"]["cells_with_D"], "no_traffic_incidents": AN["n"]["no_traffic_incidents"], "ranked": []}
for r in AN["ranked_cells"]:
    k = (r["lat0"], r["lon0"])
    place, causes = cx.get(k, (r["area"], ""))
    R["cells"]["ranked"].append({**{x: r[x] for x in ("lat0", "lon0", "D", "D_exp", "p", "area", "L1800", "n_aircraft", "n_ships", "n_people", "war", "before1900", "median_year")},
                                 "place": place, "causes": causes, "names": r["names"]})
missing = [r for r in AN["ranked_cells"] if (r["lat0"], r["lon0"]) not in cx]
assert not missing, [(r["lat0"], r["lon0"], r["names"][:2]) for r in missing]
rk = R["cells"]["ranked"]
R["cells"]["bass_cells"] = sum(1 for r in rk if r["area"] == "Bass Strait and Tasman Sea")
R["cells"]["aviation_cells"] = sum(1 for r in rk if "aviation" in r["causes"])
R["cells"]["weather_cells"] = sum(1 for r in rk if "weather" in r["causes"])
R["cells"]["war_cells"] = sum(1 for r in rk if "war" in r["causes"])

# ---------------- modern losses against modern traffic ----------------
mod = sorted([a for a in R["areas"] if a["M"]["flag"] == "higher" and a["name"] != REST], key=lambda a: -a["M"]["ratio"])
R["modern"] = {"n": R["losses"]["n2000"], "higher": [{"name": a["name"], "o": a["M"]["o"], "e": a["M"]["e"], "x": a["M"]["ratio"],
                                                       "lanes_x": a["M_lanes"]["ratio"]} for a in mod]}
GA = L[(L.area == "Gulf of Alaska") & L.year.between(2000, 2025)]
R["modern"]["alaska_o"] = len(GA); R["modern"]["alaska_wiki_pct"] = pc((GA.record == "Wikipedia list of shipwrecks").sum(), len(GA))
UA = L[(L.area == "US Atlantic coast") & L.year.between(2000, 2025)]
R["modern"]["usatl_o"] = len(UA)
US = L[L.year.between(2000, 2025)]
us_box = US.lon.between(-170, -60) & US.lat.between(17, 72)
R["modern"]["us_waters_pct"] = pc(us_box.sum(), len(US))
mx = {m["name"]: m for m in R["modern"]["higher"]}
R["modern"]["alaska_x"] = mx["Gulf of Alaska"]["x"]; R["modern"]["usatl_x"] = mx["US Atlantic coast"]["x"]

# ---------------- funnel data for the chart ----------------
R["funnel"] = AN["funnel"]
R["funnel"]["cells"] = [[round(c.D_exp, 5), int(c.D)] for c in C[(C.D > 0) & (C.D_exp > 0)].itertuples()]

# ---------------- statements made in words ----------------
assert B["flag"] == "higher (95%)" and B["lo"] > 1 and B["neigh_x"] > 2 and B["within_p"] > .3 and B["L_flag"] == "higher"
assert abs(B["o"] - B["within_e"]) < 1.5 and B["M_flag"] == "as expected" and B["famous_inside"] <= 3
assert R["dragon"]["flag"] == "as expected" and R["michigan"]["o"] == 0 and R["michigan"]["famous_inside"] == 0
assert A["North Atlantic, open ocean"]["T"]["flag"] == "as expected" and A["Mediterranean Sea"]["T"]["flag"] == "lower" and A["North Sea"]["T"]["flag"].startswith("lower")
assert A["South China Sea"]["T"]["flag"] == "as expected" and A["Gulf of Mexico"]["T"]["flag"] == "as expected"
assert A["English Channel"]["T"]["flag"] == "higher" and A["Bass Strait and Tasman Sea"]["T_lanes"]["flag"] == "higher"
assert R["worse"][0]["name"] == "Bass Strait and Tasman Sea"
assert mod[0]["name"] == "Gulf of Alaska" and R["modern"]["alaska_wiki_pct"] > 95

# ---------------- page data ----------------
KI = {k[0]: i for i, k in enumerate(KINDS)}; CI = {c[0]: i for i, c in enumerate(CONF)}
pts = []
for r in P.sort_values("year").itertuples():
    pts.append([round(r.lat, 3), round(r.lon, 3), KI[r.kind], CI[r.confidence], int(r.year) if r.year == r.year else None, r.name, NAMES.index(r.area),
                r.id, (r.location_text or "")[:160] if isinstance(r.location_text, str) else "", r.how_placed[:140], r.wikipedia_lists, 1 if isinstance(r.legend_article, str) else 0])
jsave({"rows": pts}, f"{DATA}/points.json")
LL = L.dropna(subset=["lat"])
jsave({"rows": [[round(r.lat, 2), round(r.lon, 2), int(r.year) if r.year == r.year else None, 1 if r.record.startswith("Wikipedia") else 0] for r in LL.itertuples()]},
      f"{DATA}/losses_points.json")
# sea areas, clipped to the sea and to each other, simplified
land = unary_union([shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]).buffer(0)
# Natural Earth's land fills the Great Lakes, so their outline is drawn from where AIS records ships (closed and smoothed)
import gzip as _gz
from scipy.ndimage import binary_closing, binary_fill_holes, binary_opening
import rasterio.features as rf
from rasterio.transform import from_origin
_A = np.frombuffer(_gz.open(f"{RAW6}/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz").read(), dtype="<i4").reshape(2125, 4501)
_dx, _dy = 360 / 4501, 170 / 2125
_r0, _r1, _c0, _c1 = int((85 - 49.2) / _dy), int((85 - 41) / _dy), int((-92.5 + 180) / _dx), int((-75.5 + 180) / _dx)
_M = binary_opening(binary_fill_holes(binary_closing(_A[_r0:_r1, _c0:_c1] > 0, structure=np.ones((5, 5)), iterations=2)), structure=np.ones((3, 3)))
LAKES = unary_union([shape(g) for g, v in rf.shapes(_M.astype(np.uint8), mask=_M, transform=from_origin(-180 + _c0 * _dx, 85 - _r0 * _dy, _dx, _dy)) if v == 1]).buffer(.12).buffer(-.12)
lakes_box = Polygon([(-92.5, 41.0), (-75.5, 41.0), (-75.5, 49.2), (-92.5, 49.2)])
COAST = land.simplify(.1).buffer(3.2).simplify(.05)       # within about 350 km of land: the outlines follow the coasts
taken = Polygon()
feats = []
for k, a in enumerate(AREAS):
    pa = Polygon(a[3]).buffer(0)
    pg = pa.difference(taken)
    taken = taken.union(pa)
    if a[2] == "lake" or a[0] == "Michigan Triangle":
        pg = pg.intersection(LAKES)
    elif a[2] in ("legend", "ocean"):
        pg = pg.difference(land)
    else:
        pg = pg.difference(land).intersection(COAST)
    g = pg.simplify(.04, preserve_topology=True)
    if g.is_empty:
        continue
    gj = mapping(g)
    rnd = lambda c: [[round(x, 2), round(y, 2)] for x, y in c]
    if gj["type"] == "Polygon":
        coords = [rnd(r) for r in gj["coordinates"]]
    else:
        coords = [[rnd(r) for r in poly] for poly in gj["coordinates"]]
    feats.append({"type": "Feature", "properties": {"i": k, "name": a[0]}, "geometry": {"type": gj["type"], "coordinates": coords}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/seas.json")
cells = C[(C.D > 0) | (C.L2000 > 0) | (C.L1800 > 0)]
jsave({"cell": CELL, "cols": ["lat0", "lon0", "D", "D_exp", "L2000", "L2000_exp", "D1800", "D1800_exp", "L1800", "traffic_ppm"],
       "rows": [[c.lat0, c.lon0, int(c.D), round(c.D_exp, 4), int(c.L2000), round(c.L2000_exp, 4), int(c.D1800), round(c.D1800_exp_from_losses, 4), int(c.L1800), c.traffic_share_ppm]
                for c in cells.itertuples()]}, f"{DATA}/cells.json")
SITE = {"kinds": KINDS, "conf": CONF, "areas": [[a[0], a[1], a[2]] for a in AREAS] + [[REST, "Rest", "rest"]],
        "triangles": {k: v for k, v in TRIANGLES.items()}}
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("cat", "bermuda", "dragon", "michigan")}, indent=0, ensure_ascii=False)[:6000])
print([ (w["name"], w["x"], w["lanes_x"]) for w in R["worse"]])
print(R["modern"])
for k in ("points.json", "losses_points.json", "seas.json", "cells.json"):
    print(k, os.path.getsize(f"{DATA}/{k}") // 1024, "KB")
