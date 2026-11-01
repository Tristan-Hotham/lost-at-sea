"""Reddit collage (r/dataisbeautiful style, light background), 2400 x 3000 px: world map of disappearances on
traffic with seas shaded by observed over expected, the Bermuda Triangle close up, every sea's ratio, stat tiles,
full legend and credits. Every map label is checked to sit on open sea (not land) and not over a disappearance dot;
the script stops if one fails."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from shapely.geometry import shape, Point, box as sbox
from shapely.strtree import STRtree
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
import importlib.util
from figstyle import *
from figstyle import _logtraffic

spec = importlib.util.spec_from_file_location("figs", os.path.join(ROOT, "code", "08_figures.py")); FG8 = importlib.util.module_from_spec(spec); spec.loader.exec_module(FG8)
R = jload(f"{DATA}/results.json")
P = pd.read_csv(f"{WORK}/placed.csv")
AR = {a["name"]: a for a in R["areas"]}
B = R["bermuda"]
LANDG = [shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]
LT = STRtree(LANDG)
OUT = os.path.join(ROOT, "reddit", "lost_at_sea.png")

fig = plt.figure(figsize=(24, 30), dpi=100, facecolor=BG)
# ---------------- title ----------------
fig.text(.035, .968, "Lost at sea", fontproperties=DISP, fontsize=86, color=FG, va="top")
fig.text(.035, .918, f"Is the Bermuda Triangle worse than its traffic would predict? I placed {R['cat']['placed']} famous disappearances from Wikipedia's lists on the map", fontproperties=SERP, fontsize=25, color=FG, va="top")
fig.text(.035, .9, "and compared every sea with its modern shipping. The Triangle is above its traffic, but exactly as much as its neighbours.", fontproperties=SERP, fontsize=25, color=FG, va="top")

# ---------------- world map ----------------
axm = fig.add_axes([.01, .505, .98, .385]); axm.set_facecolor(BG)
outline(axm, fc=SEA, ec="#C9C3B6", lw=1)
world(axm, ec="white", lw=.4)
seas_shade(axm, "T", alpha=.7, pale=.16)
axm.imshow(traffic_img(WORLD_EXT, EEi, 2400, 1100, alpha_max=.55), extent=WORLD_EXT, zorder=3, interpolation="bilinear")
world(axm, ec="white", lw=.4, land="none", z=4)
for nm in TRIANGLES:
    triangle(axm, nm, lw=2.2, col=FG)
for k, c in enumerate(KCOL):
    d = P[P.kind == KINDS[k][0]]
    x, y = proj(d.lon, d.lat)
    axm.scatter(x, y, s=np.where(d.confidence == "Sea area only", 16, 30), c=c, lw=.7, edgecolor="white", alpha=.92, zorder=8)
axm.set_xlim(*WORLD_EXT[:2]); axm.set_ylim(*WORLD_EXT[2:])


def tri(n, key="T"):
    t = AR[n][key]
    e = f"{t['e']:.2f}" if t["e"] < 1 else f"{t['e']:.1f}"
    return f"{t['o']} v {e}"


# labels: candidate anchors on open sea (lon, lat, ha), tried in order; the first that passes the checks is used.
# A target (lon, lat) adds a thin leader line from the label to the place it names.
nb = AR["Rest of Lake Michigan"]["T"]; gb = AR["Rest of the Great Lakes"]["T"]
cj = (AR["East China and Yellow Seas"]["T"]["o"] + AR["Sea of Japan"]["T"]["o"], AR["East China and Yellow Seas"]["T"]["e"] + AR["Sea of Japan"]["T"]["e"])
MLAB = [([(-50, 22, "left"), (-52, 18, "left"), (-48, 26, "left"), (-55, 13, "left")], f"Bermuda Triangle\n{tri('Bermuda Triangle')} expected", HOT, None),
        ([(152, 22, "left"), (155, 27, "left"), (152, 16, "left"), (170, 10, "right"), (175, 18, "right"), (165, 2, "center"), (160, 8, "center"), (162, 14, "center"), (158, 26, "center"), (163, 20, "center")], f"Dragon's Triangle\n{tri(chr(68) + 'ragon' + chr(39) + 's Triangle')}", FG, None),
        ([(118, -52, "center"), (112, -48, "center"), (125, -56, "center"), (105, -45, "center")], f"Bass Strait, Tasman Sea\n{tri('Bass Strait and Tasman Sea')}", HOT, (145, -40)),
        ([(-150, 40, "center"), (-148, 34, "center"), (-155, 45, "center"), (-140, 38, "center"), (-56, 59, "center")], f"Great Lakes\n{nb['o'] + gb['o']} v {nb['e'] + gb['e']:.1f}", HOT, (-87, 44)),
        ([(-20, -4, "center"), (-18, -12, "center"), (-22, 3, "center"), (-8, -40, "center"), (-25, -42, "center"), (-35, -30, "center"), (-15, -20, "center"), (-25, -10, "center"), (-12, -28, "center"), (-20, -32, "center")], f"Mediterranean\n{tri('Mediterranean Sea')}, fewer", COOL, (3, 38)),
        ([(160, 42, "left"), (158, 38, "left"), (162, 46, "left"), (172, 40, "right"), (175, 33, "right"), (176, 46, "right"), (170, 50, "right"), (158, 44, "center"), (160, 38, "center"), (157, 50, "center"), (162, 33, "center"), (165, 48, "center"), (168, 42, "center"), (155, 55, "center")], f"China, Japan seas\n{cj[0]} v {cj[1]:.0f}", COOL, (142, 36)),
        ([(-160, 8, "center"), (-150, 5, "center"), (-165, 14, "center"), (-140, 8, "center"), (-130, 14, "center"), (-150, -2, "center"), (-170, 32, "center"), (-125, 5, "center"), (-140, -5, "center"), (-160, -8, "center")], f"Hawaii, Dole Air Race\nmore than expected", HOT, (-157, 21))]
fig.canvas.draw()
rend = fig.canvas.get_renderer()
inv = axm.transData.inverted()
dpix = axm.transData.transform(np.column_stack(proj(P.lon, P.lat)))


def check(t, placed):
    bb = t.get_window_extent(rend).expanded(1.03, 1.08)
    W_ = fig.bbox.width
    if bb.x1 > W_ * .985 or bb.x0 < W_ * .012:
        return "off the edge"
    for gx in np.linspace(bb.x0, bb.x1, 16):
        for gy in np.linspace(bb.y0, bb.y1, 6):
            lo, la = EEi.transform(*inv.transform((gx, gy)))
            p = Point(lo, la)
            if any(LANDG[i].contains(p) for i in LT.query(p)):
                return f"land at {lo:.0f},{la:.0f}"
    LG = _logtraffic(1.1); hz = []
    for gx in np.linspace(bb.x0, bb.x1, 16):
        for gy in np.linspace(bb.y0, bb.y1, 6):
            lo, la = EEi.transform(*inv.transform((gx, gy)))
            if abs(la) < 85:
                hz.append(LG[int((85 - la) / (170 / 2125)), min(4500, int((lo + 180) / (360 / 4501)))])
    haze = float(np.mean(np.array(hz) > 4.5))
    ins = (dpix[:, 0] > bb.x0) & (dpix[:, 0] < bb.x1) & (dpix[:, 1] > bb.y0) & (dpix[:, 1] < bb.y1)
    if ins.any():
        return f"{int(ins.sum())} dots"
    for o in placed:
        if bb.overlaps(o.get_window_extent(rend)):
            return "overlaps a label"
    return ("haze", haze) if haze > .05 else None


def seg_hits(p0, p1, bb):
    for t in np.linspace(0, 1, 60):
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        if bb.x0 < x < bb.x1 and bb.y0 < y < bb.y1:
            return True
    return False


placed, leaders, problems = [], [], []
for cands, txt, col, target in MLAB:
    ok, soft = None, []
    for lon, lat, ha in cands:      # hard rules: sea only, no dots, no overlap, on the page; soft rule: clear of dense traffic haze
        x, y = EE.transform(lon, lat)
        t = axm.text(x, y, txt, ha=ha, va="center", fontsize=15 if lon > 140 else 17, color=col, fontweight="medium", zorder=12, linespacing=1.15)
        halo(t, 5, "white"); fig.canvas.draw()
        why = check(t, placed)
        t.remove()
        if why is None:
            ok = (lon, lat, ha); break
        if isinstance(why, tuple):
            soft.append((why[1], (lon, lat, ha)))
    if ok is None and soft:
        ok = min(soft)[1]
        print("  least hazy spot used for", txt.split(chr(10))[0], round(min(soft)[0], 2))
    if ok is not None:
        x, y = EE.transform(ok[0], ok[1])
        ok = axm.text(x, y, txt, ha=ok[2], va="center", fontsize=15 if ok[0] > 140 else 17, color=col, fontweight="medium", zorder=12, linespacing=1.15)
        halo(ok, 5, "white"); fig.canvas.draw()
        why = None
    if ok is None:
        problems.append((txt.split("\n")[0], why)); continue
    placed.append(ok)
    if target:
        bb = ok.get_window_extent(rend)
        tx, ty = axm.transData.transform(EE.transform(*target))
        sx = min(max(tx, bb.x0), bb.x1); sy = bb.y1 + 2 if ty > bb.y1 else bb.y0 - 2 if ty < bb.y0 else (bb.y0 + bb.y1) / 2
        leaders.append(((sx, sy), (tx, ty)))
for (p0, p1) in leaders:
    for o in placed:
        bb = o.get_window_extent(rend)
        if seg_hits(p0, (p1[0] * .97 + p0[0] * .03, p1[1] * .97 + p0[1] * .03), bb) and not (bb.x0 - 3 <= p0[0] <= bb.x1 + 3 and bb.y0 - 3 <= p0[1] <= bb.y1 + 3):
            problems.append(("leader crosses label", o.get_text().split("\n")[0]))
    a0 = inv.transform(p0); a1 = inv.transform(p1)
    axm.plot([a0[0], a1[0]], [a0[1], a1[1]], color=FG, lw=1.1, zorder=11)
    axm.scatter([a1[0]], [a1[1]], s=30, facecolor="none", edgecolor=FG, lw=1.2, zorder=11)
print("label problems:", problems)
assert not problems, problems

# ---------------- legend for the map ----------------
axl = fig.add_axes([.035, .468, .93, .034]); axl.axis("off"); axl.set_xlim(0, 1); axl.set_ylim(0, 1)
hs = [Line2D([], [], marker="o", ls="", ms=13, mfc=c, mec="white", label=k[0]) for k, c in zip(KINDS, KCOL)]
hs += [Line2D([], [], color=FG, ls=(0, (5, 3)), lw=2.2, label="the three legendary triangles")]
axl.legend(handles=hs, loc="center left", frameon=False, fontsize=16, ncol=4, bbox_to_anchor=(0, .5), handletextpad=.4, columnspacing=1.6)
axr = fig.add_axes([.68, .474, .2, .022]); axr.axis("off")
gr = np.linspace(-1.5, 2.6, 200)
axr.imshow([[rcol(10 ** v) for v in gr]], extent=(0, 1, 0, 1), aspect="auto")
axr.text(-.02, .5, "fewer", ha="right", va="center", fontsize=15, color=FG)
axr.text(1.02, .5, "more", ha="left", va="center", fontsize=15, color=FG)
fig.text(.62, .469, "Sea tint: disappearances ÷ number expected from shipping; pale: within chance.\nBlue haze: ship traffic, AIS 2015 to 2021.", va="top", fontsize=12.5, color=MUT)

# ---------------- Bermuda close-up ----------------
fig.text(.035, .448, f"Only {B['famous_inside']} of the {B['famous_n']} incidents on Wikipedia's\nBermuda Triangle page lie inside it", fontproperties=DISPB, fontsize=27, color=FG, va="top")
axb = fig.add_axes([.035, .1, .47, .3]); axb.set_facecolor(SEA)
x0, y0 = FG8.BT.transform(-88, 14.5); x1, y1 = FG8.BT.transform(-50, 42)
FG8.bermuda_map(axb, (x0, x1, y0, y1), fs=13.5, s=110)
for s_ in axb.spines.values():
    s_.set_color(RULE)
axb.set_xticks([]); axb.set_yticks([])
hb = [Line2D([], [], marker="o", ls="", ms=12, mfc=HOT, mec=HOT, label="from the article, inside"),
      Line2D([], [], marker="o", ls="", ms=12, mfc="white", mec=FG, mew=2, label="from the article, outside"),
      Line2D([], [], marker="o", ls="", ms=7, mfc="#6F757C", mec="white", label="other disappearances"),
      Line2D([], [], color=HOT, ls=(0, (5, 3)), lw=2.2, label="Miami, Bermuda, San Juan")]
axb.legend(handles=hb, loc="upper left", frameon=True, facecolor="white", edgecolor=RULE, fontsize=13.5)

# ---------------- every sea ----------------
fig.text(.54, .448, "Every sea against its traffic", fontproperties=DISPB, fontsize=27, color=FG, va="top")
fig.text(.54, .424, "observed ÷ expected, 95% interval, log scale", fontsize=14, color=MUT, va="top")
axf = fig.add_axes([.735, .1, .225, .3]); axf.set_facecolor(BG)
rows = sorted(R["areas"], key=lambda a: -(a["T"]["ratio"] or 0))
SHORT = {"Newfoundland and the Grand Banks": "Newfoundland, Grand Banks", "Malacca Strait and Andaman Sea": "Malacca, Andaman Sea", "East China and Yellow Seas": "East China, Yellow Seas",
         "North Atlantic, open ocean": "North Atlantic, open sea", "Bass Strait and Tasman Sea": "Bass Strait, Tasman Sea", "Arabian Sea and the Gulfs": "Arabian Sea, Gulfs"}
for i, a in enumerate(rows):
    t = a["T"]; y = len(rows) - i
    c = HOT if t["flag"].startswith("higher") else COOL if t["flag"].startswith("lower") else "#8A8F96"
    if a["group"] == "legend":
        axf.axhspan(y - .5, y + .5, xmin=-1.1, color=GOLD, alpha=.2, lw=0, clip_on=False)
    axf.plot([max(t["lo"], .02), min(t["hi"], 900)], [y, y], color=c, lw=4, solid_capstyle="round", alpha=.55 if t["flag"] == "as expected" else .95)
    if t["ratio"]:
        axf.scatter([t["ratio"]], [y], s=70, color=c, edgecolor="white", zorder=3)
    else:
        axf.annotate("", xy=(.02, y), xytext=(.06, y), arrowprops=dict(arrowstyle="->", color=c, lw=2.5))
axf.set_yticks(range(len(rows), 0, -1)); axf.set_yticklabels([SHORT.get(a["name"], a["name"]) for a in rows], fontsize=13)
for lab, a in zip(axf.get_yticklabels(), rows):
    if a["group"] == "legend":
        lab.set_fontweight("bold")
axf.set_xscale("log"); axf.set_xlim(.02, 900); axf.axvline(1, color=FG, lw=1.5)
axf.set_xticks([.1, 1, 10, 100]); axf.set_xticklabels(["0.1", "1", "10", "100"], fontsize=13)
axf.grid(axis="x", color=RULE); axf.set_axisbelow(True); spines(axf); axf.spines["left"].set_visible(False); axf.tick_params(axis="y", length=0)
axf.set_ylim(.4, len(rows) + .6)
fl = [Line2D([], [], color=HOT, lw=4, label="more than expected"), Line2D([], [], color="#8A8F96", lw=4, label="within chance"), Line2D([], [], color=COOL, lw=4, label="fewer than expected")]
fig.text(.54, .41, "red: more than expected  ·  grey: within chance  ·  blue: fewer", fontsize=14, color=MUT, va="top")

# ---------------- stat tiles ----------------
tiles = [(f"{B['o']} v {B['e']:.1f}", "disappearances in the Bermuda Triangle\nagainst the number its shipping predicts", HOT),
         (f"{B['neigh_x']:.1f}×", "the excess of its four neighbours,\nthe same as the Triangle's own", GOLD),
         (f"{B['within_e']:.1f}", f"expected in the Triangle given its share\nof its region's traffic: it has {B['o']}", INK),
         (f"{R['worse'][0]['o']} v {R['worse'][0]['e']:.2f}", "Bass Strait and the Tasman Sea: colonial\nschooners in a stormy strait", "#7A1020")]
for i, (big, small, col) in enumerate(tiles):
    x = .035 + i * .235
    fig.add_artist(FancyBboxPatch((x, .043), .218, .042, boxstyle="square,pad=0", fc="white", ec=RULE, lw=1.2, transform=fig.transFigure))
    fig.text(x + .012, .074, big, fontproperties=DISP, fontsize=34, color=col, va="center")
    fig.text(x + .012, .056, small, fontsize=13, color=MUT, va="center", linespacing=1.3)

# ---------------- credits ----------------
fig.text(.035, .027, "Sources: Wikipedia contributors, lists of missing ships, missing aircraft and people who disappeared mysteriously at sea, and the three triangle articles (CC BY-SA 4.0); World Bank, Global Shipping Traffic Density",
         fontsize=12.5, color=MUT)
fig.text(.035, .016, "(IMF and World Bank, AIS 2015 to 2021, CC BY 4.0), a modern proxy only; Natural Earth. Placements from the location text are approximate. Famous disappearances, not all losses.", fontsize=12.5, color=MUT)
fig.text(.035, .005, "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/lost-at-sea", fontsize=12.5, color=FG)
fig.savefig(OUT, dpi=100, facecolor=BG)
from PIL import Image
print(OUT, Image.open(OUT).size)
