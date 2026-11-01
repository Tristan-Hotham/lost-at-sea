"""Observed against expected: famous disappearances and recorded losses against modern traffic and against all recorded
losses, for named sea areas and 2 degree cells, with exact Poisson intervals and funnel limits.

Tests (O observed, E expected, ratio O/E):
  T  disappearances against traffic: E = (all placed disappearances) x (area's share of the AIS traffic index).
     Areas use every placed incident; cells use only incidents placed by a position, a named place or a route
     midpoint (not "sea area only").
  L  disappearances against recorded losses, 1800 to 2025: E = (placed disappearances of 1800 to 2025) x (area's share
     of recorded losses of 1800 to 2025). This keeps the denominator from the same era as the numerator.
  M  modern recorded losses (2000 to 2025) against traffic (AIS 2015 to 2021): the closest match of eras.
Sensitivities: the "lanes" traffic index (sampled pixels with at least 1,000 AIS positions, less sensitive to how
densely receivers pick up ships), disappearances since 1946 only, ships only, and placed-by-position-or-place only.
95% intervals are exact Poisson intervals for O, divided by E. Funnel limits (95% and 99.8%) follow Spiegelhalter's
interpolated Poisson quantiles. Output: data/areas.csv, data/cells.csv, WORK/analysis.json."""
import numpy as np
import pandas as pd
from scipy.stats import chi2, poisson
from matplotlib.path import Path
from common import *
from areas import AREAS, NAMES, REST

TR = np.load(f"{WORK}/traffic.npz")
D = pd.read_csv(f"{DATA}/disappearances.csv")
L = pd.read_csv(f"{DATA}/losses.csv")
NR, NC = TR["csum"].shape
P = D[D.lat.notna()].copy()
P["conf_i"] = P.confidence.map({c[0]: i for i, c in enumerate(CONF)})
P["row"] = ((85 - P.lat) // CELL).clip(0, NR - 1).astype(int)
P["col"] = ((P.lon + 180) // CELL).clip(0, NC - 1).astype(int)
pts = P[["lon", "lat"]].to_numpy()
own = np.full(len(P), len(AREAS)); free = np.ones(len(P), bool)
seaonly = (P.conf_i == 3).to_numpy()
for k, a in enumerate(AREAS):
    ins = Path(a[3] + [a[3][0]]).contains_points(pts) & free
    if a[2] == "legend":           # an incident placed only by a named sea is never counted inside a legendary triangle
        ins &= ~seaonly
    own[ins] = k; free &= ~ins
P["area"] = [NAMES[k] for k in own]
P.to_csv(f"{WORK}/placed.csv", index=False)


def ci(o, e, a=.05):
    lo = chi2.ppf(a / 2, 2 * o) / 2 / e if o > 0 else 0.0
    hi = chi2.ppf(1 - a / 2, 2 * o + 2) / 2 / e
    return lo, hi


def p_upper(o, e):
    """One-sided P(X >= o) for X ~ Poisson(e)."""
    return float(poisson.sf(o - 1, e)) if o > 0 else 1.0


def p_lower(o, e):
    return float(poisson.cdf(o, e))


def funnel(e, p):
    """Funnel limit for the ratio O/E at expected count e and probability p, using the gamma (continuous Poisson)
    quantiles: upper limits from Gamma(e + 1), lower limits from Gamma(e). Smooth in e, and close to the exact
    Poisson limits."""
    from scipy.stats import gamma
    return float(gamma.ppf(p, e + 1) / e) if p > .5 else float(gamma.ppf(p, e) / e)


def test(o, e):
    lo, hi = ci(o, e)
    pu, pl = p_upper(o, e), p_lower(o, e)
    flag = "higher" if pu < .001 else "lower" if pl < .001 else "higher (95%)" if pu < .025 else "lower (95%)" if pl < .025 else "as expected"
    return {"o": int(o), "e": round(float(e), 3), "ratio": round(float(o / e), 3) if e > 0 else None, "lo": round(float(lo), 3),
            "hi": round(float(hi), 3), "p_up": pu, "p_lo": pl, "flag": flag}


# ---------------- areas ----------------
T_sum = TR["asum"]; T_tot = float(TR["tot"])
LANES = jload(f"{WORK}/lanes.json") if os.path.exists(f"{WORK}/lanes.json") else None
Ly = L[L.year.between(1800, 2025)]
Lm = L[L.year.between(2000, 2025)]
L15 = L[L.year.between(2015, 2025)]
P18 = P[P.year.between(1800, 2025)]
P46 = P[P.year.between(1946, 2025)]
PS = P[P.kind == "Ship or boat"]
PLST = P[P.wikipedia_lists != "legend article"]          # leaves out incidents known only from the three legend articles
PP = P[P.conf_i <= 1]
Lpeace = L[L.year.between(1800, 2025) & ~L.war_year]
P18peace = P18[~(P18.year.between(1914, 1918) | P18.year.between(1939, 1945))]
rows = []
for k, nm in enumerate(NAMES):
    sh = T_sum[k] / T_tot
    lsh = LANES["share"][k] if LANES else None
    o = (P.area == nm).sum()
    r = {"area": nm, "short": AREAS[k][1] if k < len(AREAS) else "Rest", "group": AREAS[k][2] if k < len(AREAS) else "rest",
         "traffic_share_pct": round(100 * sh, 3), "lanes_share_pct": round(100 * lsh, 3) if lsh is not None else None,
         "T": test(o, len(P) * sh),
         "T_lanes": test(o, len(P) * lsh) if lsh is not None else None,
         "T_1946": test((P46.area == nm).sum(), len(P46) * sh),
         "T_ships": test((PS.area == nm).sum(), len(PS) * sh),
         "T_placed": test((PP.area == nm).sum(), len(PP) * sh),
         "T_lists": test((PLST.area == nm).sum(), len(PLST) * sh),
         "L": test((P18.area == nm).sum(), len(P18) * (Ly.area == nm).sum() / len(Ly)) if (Ly.area == nm).sum() else None,
         "L_peace": test((P18peace.area == nm).sum(), len(P18peace) * (Lpeace.area == nm).sum() / len(Lpeace)) if (Lpeace.area == nm).sum() else None,
         "M": test((Lm.area == nm).sum(), len(Lm) * sh),
         "M_lanes": test((Lm.area == nm).sum(), len(Lm) * lsh) if lsh is not None else None,
         "M15": test((L15.area == nm).sum(), len(L15) * sh),
         "losses_1800": int((Ly.area == nm).sum()), "losses_2000": int((Lm.area == nm).sum()),
         "kinds": {kd[0]: int(((P.area == nm) & (P.kind == kd[0])).sum()) for kd in KINDS},
         "median_year": int(P[P.area == nm].year.median()) if (P.area == nm).sum() else None,
         "conf": {c[0]: int(((P.area == nm) & (P.confidence == c[0])).sum()) for c in CONF}}
    rows.append(r)
AR = {r["area"]: r for r in rows}

# Bermuda against its neighbours: is it worse than the rest of the western North Atlantic?
from scipy.stats import binomtest
NB = ["US Atlantic coast", "Caribbean Sea", "Gulf of Mexico", "Newfoundland and the Grand Banks"]
ib = NAMES.index("Bermuda Triangle"); inb = [NAMES.index(n) for n in NB]
ob = int((P.area == "Bermuda Triangle").sum()); onb = int(P.area.isin(NB).sum())
tb, tnb = T_sum[ib], sum(T_sum[i] for i in inb)
bt = binomtest(ob, ob + onb, tb / (tb + tnb), alternative="greater")
lb, lnb = int((Ly.area == "Bermuda Triangle").sum()), int(Ly.area.isin(NB).sum())
ob18, onb18 = int((P18.area == "Bermuda Triangle").sum()), int(P18.area.isin(NB).sum())
bt2 = binomtest(ob18, ob18 + onb18, lb / (lb + lnb), alternative="greater")
NEIGH = {"names": NB, "o_bermuda": ob, "o_neigh": onb, "traffic_share_bermuda_within": round(float(tb / (tb + tnb)), 4),
         "expected_bermuda_within": round(float((ob + onb) * tb / (tb + tnb)), 2), "p": float(bt.pvalue),
         "neigh_T": test(onb, len(P) * tnb / T_tot),
         "o18_bermuda": ob18, "o18_neigh": onb18, "loss_share_bermuda_within": round(lb / (lb + lnb), 4),
         "expected18_bermuda_within": round((ob18 + onb18) * lb / (lb + lnb), 2), "p_losses": float(bt2.pvalue),
         "losses_bermuda": lb, "losses_neigh": lnb}
print("neighbours", NEIGH)
print(P[P.area == "Bermuda Triangle"][["name", "year", "kind", "confidence", "wikipedia_lists", "legend_article"]].to_string())
BA = D[D.legend_article.fillna("").str.contains("Bermuda")]
print(BA[["name", "year", "lat", "lon", "confidence"]].to_string())

# ---------------- cells ----------------
cs, cnz = TR["csum"], TR["cnz"]
Pc = P[P.conf_i <= 2]
Dg = np.zeros((NR, NC)); np.add.at(Dg, (Pc.row.to_numpy(), Pc.col.to_numpy()), 1)
Lg = np.zeros((NR, NC)); np.add.at(Lg, (Ly.row.to_numpy(), Ly.col.to_numpy()), 1)
Mg = np.zeros((NR, NC)); np.add.at(Mg, (Lm.row.to_numpy(), Lm.col.to_numpy()), 1)
D18 = Pc[Pc.year.between(1800, 2025)]
D18g = np.zeros((NR, NC)); np.add.at(D18g, (D18.row.to_numpy(), D18.col.to_numpy()), 1)
Nd, Nm = len(Pc), len(Lm)
no_traffic = int(Dg[cs == 0].sum())
cells = []
for i in range(NR):
    for j in range(NC):
        if cs[i, j] == 0 and Dg[i, j] == 0 and Lg[i, j] == 0:
            continue
        lat0, lon0 = 85 - (i + 1) * CELL, -180 + j * CELL
        e = Nd * cs[i, j] / T_tot
        em = Nm * cs[i, j] / T_tot
        el = len(D18) * Lg[i, j] / len(Ly)
        c = {"row": i, "col": j, "lat0": lat0, "lon0": lon0, "traffic_share_ppm": round(1e6 * cs[i, j] / T_tot, 2),
             "D": int(Dg[i, j]), "D_exp": round(e, 4), "L1800": int(Lg[i, j]), "L2000": int(Mg[i, j]), "L2000_exp": round(em, 4),
             "D1800": int(D18g[i, j]), "D1800_exp_from_losses": round(el, 4)}
        c["D_ratio"] = round(c["D"] / e, 2) if e > 0 else None
        c["D_p_up"] = p_upper(c["D"], e) if e > 0 else None
        c["M_ratio"] = round(c["L2000"] / em, 2) if em > 0 else None
        c["M_p_up"] = p_upper(c["L2000"], em) if em > 0 else None
        c["DL_ratio"] = round(c["D1800"] / el, 2) if el > 0 else None
        c["DL_p_up"] = p_upper(c["D1800"], el) if el > 0 else None
        cells.append(c)
C = pd.DataFrame(cells)
C.to_csv(f"{DATA}/cells.csv", index=False)

# ranked cells: disappearances against traffic, at least 2 incidents, beyond the 99.8% funnel
ip = {(r.row, r.col): r for r in Pc.itertuples()}
flag = C[(C.D >= 2) & C.D_p_up.notna() & (C.D_p_up < .001)].sort_values("D_p_up")
ranked = []
for c in flag.itertuples():
    inc = Pc[(Pc.row == c.row) & (Pc.col == c.col)].sort_values("year")
    areas = inc.area.value_counts()
    ranked.append({"row": int(c.row), "col": int(c.col), "lat0": c.lat0, "lon0": c.lon0, "D": int(c.D), "D_exp": c.D_exp,
                   "ratio": c.D_ratio, "p": c.D_p_up, "area": areas.index[0], "traffic_share_ppm": c.traffic_share_ppm,
                   "L1800": int(c.L1800), "n_aircraft": int((inc.kind == "Aircraft").sum()), "n_ships": int((inc.kind == "Ship or boat").sum()),
                   "n_people": int((inc.kind == "People lost at sea").sum()),
                   "war": int((inc.year.between(1914, 1918) | inc.year.between(1939, 1945)).sum()),
                   "before1900": int((inc.year < 1900).sum()), "median_year": int(inc.year.median()),
                   "names": [f"{n} ({int(y) if y == y else '?'})" for n, y in zip(inc.name, inc.year)]})

# funnel curve
ex = np.logspace(-3, 2.2, 140)
FUN = {"e": [round(float(x), 5) for x in ex],
       "u95": [round(funnel(x, .975), 4) for x in ex], "u998": [round(funnel(x, .999), 4) for x in ex],
       "l95": [round(funnel(x, .025), 4) for x in ex], "l998": [round(funnel(x, .001), 4) for x in ex]}

out = {"areas": rows, "ranked_cells": ranked, "funnel": FUN, "neighbours": NEIGH,
       "n": {"placed": len(P), "placed_cells": len(Pc), "placed_1800": len(P18), "placed_1946": len(P46), "placed_ships": len(PS),
             "placed_pos_place": len(PP), "placed_lists": len(PLST), "losses_1800": len(Ly), "losses_2000": len(Lm), "losses_2015": len(L15),
             "no_traffic_incidents": no_traffic, "cells_with_traffic": int((cs > 0).sum()), "cells_flagged": len(flag),
             "cells_with_D": int((C.D > 0).sum())}}
jsave(out, f"{WORK}/analysis.json")
A = pd.DataFrame([{"area": r["area"], "traffic_share_pct": r["traffic_share_pct"], "lanes_share_pct": r["lanes_share_pct"],
                   "disappearances": r["T"]["o"], "expected_from_traffic": r["T"]["e"], "ratio": r["T"]["ratio"], "ci95_low": r["T"]["lo"],
                   "ci95_high": r["T"]["hi"], "verdict": r["T"]["flag"],
                   "disappearances_1800_2025": r["L"]["o"] if r["L"] else None, "expected_from_recorded_losses": r["L"]["e"] if r["L"] else None,
                   "ratio_vs_losses": r["L"]["ratio"] if r["L"] else None, "verdict_vs_losses": r["L"]["flag"] if r["L"] else None,
                   "recorded_losses_1800_2025": r["losses_1800"], "recorded_losses_2000_2025": r["losses_2000"],
                   "expected_modern_losses_from_traffic": r["M"]["e"], "ratio_modern_losses": r["M"]["ratio"], "verdict_modern_losses": r["M"]["flag"]}
                  for r in rows])
A.to_csv(f"{DATA}/areas.csv", index=False)
pd.set_option("display.width", 250)
print(A[["area", "traffic_share_pct", "lanes_share_pct", "disappearances", "expected_from_traffic", "ratio", "ci95_low", "ci95_high", "verdict",
         "ratio_vs_losses", "verdict_vs_losses", "recorded_losses_2000_2025", "ratio_modern_losses", "verdict_modern_losses"]].to_string())
print(out["n"])
for r in ranked[:15]:
    print(r["area"], r["lat0"], r["lon0"], r["D"], r["D_exp"], r["ratio"], f"{r['p']:.1e}", r["n_aircraft"], r["war"], r["before1900"], r["names"][:4])
