"""All recorded losses with a position, as the comparison for the famous disappearances.

From the world-shipwrecks study's cleaned wrecks (data/wrecks.csv there) I keep only the two global records:
  source 4  entries of Wikipedia's "List of shipwrecks" pages that give coordinates (CC BY-SA 4.0), and
  source 2  Wikidata wrecks outside the Scottish and Welsh bulk imports (CC0).
The bulk national imports (Canmore for Scotland, Coflein for Wales) and NOAA's AWOIS (United States waters only) are
left out, because they would make the seas of three countries look far more dangerous than everywhere else. Each wreck
gets its 2 degree cell and its named sea area. Output: data/losses.csv (id, source, name, year, cause group, war year,
cell, area) and WORK/losses_points.json for the page."""
import numpy as np
import pandas as pd
from matplotlib.path import Path
from common import *
from areas import AREAS, NAMES, REST

W = pd.read_csv(WRECKS, low_memory=False, usecols=["id", "source", "name", "lat", "lon", "year", "cause"])
n_all = len(W)
W = W[W.source.isin([2, 4])].copy()
W = W[W.lat.between(-85, 85)].copy()
CAUSE = ["War", "Foundered or storm", "Wrecked or ran aground", "Collision", "Fire or explosion", "Scuttled", "Accident", "Not recorded"]
W["cause_group"] = W.cause.fillna(7).astype(int).map(lambda c: CAUSE[c])
W["record"] = W.source.map({2: "Wikidata", 4: "Wikipedia list of shipwrecks"})
W["war_year"] = W.year.between(1914, 1918) | W.year.between(1939, 1945)
W["row"] = ((85 - W.lat) // CELL).clip(0, int(170 / CELL) - 1).astype(int)
W["col"] = ((W.lon + 180) // CELL).clip(0, int(360 / CELL) - 1).astype(int)
pts = W[["lon", "lat"]].to_numpy()
own = np.full(len(W), len(AREAS)); free = np.ones(len(W), bool)
for k, a in enumerate(AREAS):
    ins = Path(a[3] + [a[3][0]]).contains_points(pts) & free
    own[ins] = k; free &= ~ins
W["area"] = [NAMES[k] for k in own]
W["year"] = W.year.astype("Int64")
out = W[["id", "record", "name", "lat", "lon", "year", "cause_group", "war_year", "row", "col", "area"]]
out.to_csv(f"{DATA}/losses.csv", index=False)
jsave({"n_source_file": n_all, "n_kept": len(W), "n_wikipedia": int((W.source == 4).sum()), "n_wikidata": int((W.source == 2).sum())},
      f"{WORK}/losses_meta.json")
print(len(W), "losses;", W.year.notna().sum(), "dated;", W.year.between(1800, 2025).sum(), "1800 to 2025;", W.year.between(2000, 2025).sum(), "2000 to 2025")
print(W[W.year.between(1800, 2025)].area.value_counts().head(12))
