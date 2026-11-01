"""Static figures: header.png (1200 x 630), paper figures (release/paper/f_*.png) and blog figures (release/blog/b_*.png).
All numbers come from data/results.json."""
import shutil
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
P = pd.read_csv(f"{WORK}/placed.csv")
PAP = os.path.join(ROOT, "release", "paper"); BLG = os.path.join(ROOT, "release", "blog")
for d in (PAP, BLG):
    os.makedirs(d, exist_ok=True)
AR = {a["name"]: a for a in R["areas"]}
KI = {k[0]: i for i, k in enumerate(KINDS)}


def save(fig, name, blog=True):
    fig.savefig(f"{PAP}/f_{name}.png", dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(f"{BLG}/b_{name}.png", dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)


def dots(ax, D, tr=EE, s=14, z=8, alpha=.9):
    for k, c in enumerate(KCOL):
        d = D[D.kind == KINDS[k][0]]
        x, y = proj(d.lon, d.lat, tr)
        ax.scatter(x, y, s=np.where(d.confidence == "Sea area only", s * .6, s), c=c, lw=.5, edgecolor="white", alpha=alpha, zorder=z)


# ---------- world map ----------
def fig_map():
    fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
    ax = fig.add_axes([0, .04, 1, .9]); ax.set_facecolor(BG)
    outline(ax, fc=SEA, ec="#C9C3B6", lw=.6)
    world(ax, ec="white", lw=.25)
    seas_shade(ax, "T", alpha=.55, pale=.18)
    img = traffic_img(WORLD_EXT, EEi, 2400, 1100, alpha_max=.75)
    ax.imshow(img, extent=WORLD_EXT, zorder=3, interpolation="bilinear")
    world(ax, ec="white", lw=.25, land="none", z=4)
    for nm in TRIANGLES:
        triangle(ax, nm, lw=1.3, col=FG)
    dots(ax, P, s=10)
    ax.set_xlim(*WORLD_EXT[:2]); ax.set_ylim(*WORLD_EXT[2:])
    fig.text(.02, .955, f"{R['cat']['placed']} famous disappearances at sea, on modern shipping traffic", fontproperties=DISPB, fontsize=17, color=FG)
    hs = [Line2D([], [], marker="o", ls="", ms=7, mfc=c, mec="white", label=k[0]) for k, c in zip(KINDS, KCOL)]
    hs += [Line2D([], [], color=FG, ls=(0, (5, 3)), lw=1.3, label="the three triangles")]
    ax.legend(handles=hs, loc="lower left", frameon=False, fontsize=10, ncol=4, bbox_to_anchor=(0.01, -0.04))
    fig.text(.99, .012, "Shading: disappearances against traffic (red more, blue fewer, pale within chance). Traffic: World Bank / IMF AIS density 2015 to 2021.", ha="right", fontsize=8, color=MUT)
    save(fig, "map")


# ---------- decades ----------
def fig_decades():
    d = R["cat"]["decades"]
    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=BG); ax.set_facecolor(BG)
    x = np.array([r["dec"] for r in d]); acc = np.zeros(len(d))
    for k, c in zip(KINDS, KCOL):
        v = np.array([r[k[0]] for r in d]); ax.bar(x + 5, v, 8.4, bottom=acc, color=c, label=k[0]); acc += v
    for w in (1910, 1940):
        ax.axvspan(w, w + 10, color=HOT, alpha=.08, lw=0)
    spines(ax); ax.set_xlim(1797, 2033); ax.set_ylabel("disappearances per decade")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_title("Famous disappearances placed at sea, per decade", loc="left", fontproperties=DISPB, fontsize=15)
    fig.tight_layout(); save(fig, "decades")


# ---------- forest ----------
def fig_forest(key="T", name="forest", title="Disappearances against traffic, by sea"):
    rows = sorted([a for a in R["areas"] if a[key]], key=lambda a: -(a[key]["ratio"] or 0))
    fig, ax = plt.subplots(figsize=(9, 9), facecolor=BG); ax.set_facecolor(BG)
    for i, a in enumerate(rows):
        t = a[key]; y = len(rows) - i
        c = HOT if t["flag"].startswith("higher") else COOL if t["flag"].startswith("lower") else "#8A8F96"
        if a["group"] == "legend":
            ax.axhspan(y - .5, y + .5, color=GOLD, alpha=.16, lw=0)
        ax.plot([max(t["lo"], .02), min(t["hi"], 900)], [y, y], color=c, lw=3, solid_capstyle="round", alpha=.6 if t["flag"] == "as expected" else .95)
        if t["ratio"] and t["ratio"] > 0:
            ax.scatter([t["ratio"]], [y], s=40, color=c, edgecolor="white", zorder=3)
        else:
            ax.annotate("", xy=(.02, y), xytext=(.05, y), arrowprops=dict(arrowstyle="->", color=c, lw=2))
        ax.text(1100, y, f"{t['o']} v {t['e']:.2f}" if t["e"] < 1 else f"{t['o']} v {t['e']:.1f}", va="center", fontsize=9, color=MUT)
    ax.set_yticks(range(len(rows), 0, -1)); ax.set_yticklabels([a["name"] for a in rows], fontsize=10)
    for lab, a in zip(ax.get_yticklabels(), rows):
        if a["group"] == "legend":
            lab.set_fontweight("bold")
    ax.set_xscale("log"); ax.set_xlim(.02, 900); ax.axvline(1, color=FG, lw=1.2)
    ax.set_xticks([.03, .1, .3, 1, 3, 10, 30, 100, 300]); ax.set_xticklabels(["0.03", "0.1", "0.3", "1", "3", "10", "30", "100", "300"])
    ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True); spines(ax); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.set_xlabel("observed ÷ expected (log scale), with exact 95% interval")
    ax.set_title(title, loc="left", fontproperties=DISPB, fontsize=15)
    fig.text(.99, .01, "observed v expected at right", ha="right", fontsize=8, color=MUT)
    fig.tight_layout(); save(fig, name)


# ---------- funnel ----------
def fig_funnel():
    F = R["funnel"]
    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG); ax.set_facecolor(BG)
    e = np.array(F["e"])
    for k, ls, lw in (("u998", (0, (5, 3)), 1.5), ("u95", (0, (2, 3)), 1.2), ("l95", (0, (2, 3)), 1.2), ("l998", (0, (5, 3)), 1.5)):
        v = np.array(F[k]); ok = v > 0
        ax.plot(e[ok], v[ok], color=MUT, ls=ls, lw=lw)
    cells = np.array(F["cells"])
    ax.scatter(cells[:, 0], cells[:, 1] / cells[:, 0], s=6, color="#B9B3A6", alpha=.5, lw=0, zorder=2, label="2 degree squares with a disappearance")
    lab = {"Bermuda Triangle": (0, 10, "center"), "Dragon's Triangle": (8, -12, "left"), "Bass Strait and Tasman Sea": (8, 0, "left"), "Rest of Lake Michigan": (8, 0, "left"),
           "Rest of the Great Lakes": (8, 0, "left"), "Mediterranean Sea": (0, -14, "center"), "North Atlantic, open ocean": (-8, 8, "right"), "Sea of Japan": (-8, 0, "right")}
    for a in R["areas"]:
        t = a["T"]
        r = t["o"] / t["e"] if t["o"] else .03
        c = HOT if t["flag"].startswith("higher") else COOL if t["flag"].startswith("lower") else "#6F757C"
        ax.scatter([t["e"]], [r], s=70 if a["group"] == "legend" else 42, color=c, edgecolor=FG if a["group"] == "legend" else "white", lw=1.4 if a["group"] == "legend" else .8, zorder=4)
        if a["name"] in lab:
            dx, dy, ha = lab[a["name"]]
            nm = a["name"].replace(", open ocean", "").replace("Rest of Lake", "Lake").replace("Rest of the Great Lakes", "Other Great Lakes")
            if a["name"] == "Michigan Triangle":
                nm = "Michigan Triangle (none)"
            halo(ax.annotate(nm, (t["e"], r), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=10, fontweight="bold" if a["group"] == "legend" else "normal"), 3, BG)
    mt = AR["Michigan Triangle"]["T"]
    ax.scatter([mt["e"]], [.03], s=70, color="#6F757C", edgecolor=FG, lw=1.4, zorder=4)
    halo(ax.annotate("Michigan Triangle (none observed)", (mt["e"], .03), xytext=(8, 0), textcoords="offset points", va="center", fontsize=10, fontweight="bold"), 3, BG)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(.01, 160); ax.set_ylim(.025, 3000)
    from matplotlib.ticker import FuncFormatter
    ff = FuncFormatter(lambda v, _: f"{v:g}")
    ax.xaxis.set_major_formatter(ff); ax.yaxis.set_major_formatter(ff)
    ax.axhline(1, color=FG, lw=1.1); spines(ax); ax.grid(color=RULE, lw=.6); ax.set_axisbelow(True)
    ax.set_xlabel("expected number of disappearances (from traffic)"); ax.set_ylabel("observed ÷ expected")
    ax.set_title("Funnel plot: every sea against its traffic", loc="left", fontproperties=DISPB, fontsize=15)
    hs = [Line2D([], [], color=MUT, ls=(0, (5, 3)), label="99.8% limits"), Line2D([], [], color=MUT, ls=(0, (2, 3)), label="95% limits"),
          Line2D([], [], marker="o", ls="", color="#B9B3A6", label="2 degree squares")]
    ax.legend(handles=hs, frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout(); save(fig, "funnel")


# ---------- the Bermuda Triangle ----------
LAEA = "+proj=laea +lat_0=29 +lon_0=-68 +datum=WGS84"
BT = Transformer.from_crs(4326, LAEA, always_xy=True); BTi = Transformer.from_crs(LAEA, 4326, always_xy=True)
FAMLAB = {  # name -> (label, dx, dy, ha) offsets in points; every label sits on open sea
    "Flight 19": ("Flight 19, 1945", 0, 0, "left"), "PBM Mariner (Flight 19 search)": ("PBM Mariner, 1945", 0, 0, "left"),
    "Airborne Transport DC-3": ("DC-3, 1948", 0, 0, "left"), "SS Cotopaxi": ("Cotopaxi, 1925", 0, 0, "left"),
    "Carroll A. Deering": ("Carroll A. Deering, 1921", 12, 2, "left"), "KC-135 Stratotankers": ("KC-135s, 1963", 12, 2, "left"),
    "Connemara IV": ("Connemara IV, 1955", 12, 2, "left"), "USS Cyclops": ("USS Cyclops, 1918", 12, -8, "left"),
    "BSAA Star Ariel": ("Star Ariel, 1949", -4, 17, "center"), "USS Nereus": ("USS Nereus, 1941", 12, -2, "left"),
    "USS Proteus": ("USS Proteus, 1941 (Caribbean)", 0, -16, "center"), "SS Marine Sulphur Queen": ("Marine Sulphur\nQueen, 1963", 0, -24, "center"),
    "BSAA Star Tiger, with Sir Arthur Coningham": ("Star Tiger, 1948", -12, 2, "right"), "HMS Atalanta": ("HMS Atalanta, 1880", 12, 2, "left")}
STACK = ["SS Cotopaxi", "PBM Mariner (Flight 19 search)", "Flight 19", "Airborne Transport DC-3"]   # the Florida coast cluster


def bermuda_map(ax, ext, labels=True, fs=9.5, s=60, shade=False):
    world(ax, tr=BT, ext=ext, clip=(-110, 0, -20, 60), lw=.4)
    if shade:
        seas_shade(ax, "T", tr=BT, alpha=.45, pale=.18, only=["Bermuda Triangle"])
    ax.imshow(traffic_img(ext, BTi, 1000, int(1000 * (ext[3] - ext[2]) / (ext[1] - ext[0])), alpha_max=.45, blur=2.6, lo=3.2), extent=ext, zorder=3, interpolation="bilinear")
    world(ax, tr=BT, ext=ext, clip=(-110, 0, -20, 60), lw=.4, land="none", z=4)
    triangle(ax, "Bermuda Triangle", tr=BT, lw=2.2, col=HOT)
    others = P[(P.lon.between(-100, -30)) & (P.lat.between(5, 55))]
    x, y = proj(others.lon, others.lat, BT); ax.scatter(x, y, s=16, color="#6F757C", alpha=.75, lw=.4, edgecolor="white", zorder=5)
    fam = R["famous"]["Bermuda Triangle"]["list"]
    pos = {}
    for f in fam:
        if f.get("lat") is None:
            continue
        x, y = BT.transform(f["lon"], f["lat"])
        if not (ext[0] < x < ext[1] and ext[2] < y < ext[3]):
            continue
        pos[f["name"]] = (x, y)
        ax.scatter([x], [y], s=s, color=HOT if f["inside"] else "white", edgecolor=HOT if f["inside"] else FG, lw=1.6, zorder=8, marker="o")
    if labels:
        # the Florida cluster: a stacked column out at sea, east of the coast, with short leaders that do not cross
        st = [n for n in STACK if n in pos]
        st.sort(key=lambda n: -pos[n][1])
        xs = max(pos[n][0] for n in st) + 1.5e5
        ytop = pos[st[0]][1] + 3.5e5
        for k, n in enumerate(st):
            yl = ytop - k * 1.15e5
            ax.plot([pos[n][0] + 2e4, xs - 1.5e4], [pos[n][1], yl], color=FG, lw=.7, zorder=7)
            halo(ax.text(xs, yl, FAMLAB[n][0], ha="left", va="center", fontsize=fs, color=FG, zorder=9), 3.2, "white")
        for n, (x, y) in pos.items():
            if n in STACK or n not in FAMLAB:
                continue
            lab, dx, dy, ha = FAMLAB[n]
            halo(ax.annotate(lab, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=fs, color=FG, zorder=9), 3.2, "white")
    for v in TRIANGLES["Bermuda Triangle"]["verts"]:
        x, y = BT.transform(v[0], v[1])
        ax.scatter([x], [y], s=26, color=HOT, zorder=7, marker="s")


def fig_bermuda():
    fig = plt.figure(figsize=(11, 8.2), facecolor=BG)
    ax = fig.add_axes([.01, .07, .98, .84]); ax.set_facecolor(SEA)
    x0, y0 = BT.transform(-88, 14); x1, y1 = BT.transform(-44, 44)
    ext = (x0, x1 + 3e5, y0, y1)
    bermuda_map(ax, ext)
    a = R["bermuda"]
    fig.text(.02, .95, f"Only {a['famous_inside']} of the {a['famous_n']} incidents on Wikipedia's Bermuda Triangle page lie inside it", fontproperties=DISPB, fontsize=16, color=FG)
    hs = [Line2D([], [], marker="o", ls="", ms=8, mfc=HOT, mec=HOT, label="incident from the article, inside"),
          Line2D([], [], marker="o", ls="", ms=8, mfc="white", mec=FG, label="incident from the article, outside"),
          Line2D([], [], marker="o", ls="", ms=5, mfc="#8A8F96", mec="none", label="other disappearances"),
          Line2D([], [], color=HOT, ls=(0, (5, 3)), lw=2, label="Miami, Bermuda, San Juan")]
    ax.legend(handles=hs, loc="upper left", frameon=True, facecolor="white", edgecolor=RULE, fontsize=9.5)
    fig.text(.02, .035, "Positions as placed from the text: route midpoints and 'off' a place are approximate. HMS Atalanta (1880) lies off the map, in mid-Atlantic.", fontsize=8, color=MUT)
    fig.text(.02, .012, "Blue haze: ship traffic, World Bank / IMF AIS density 2015 to 2021. Grey dots: other disappearances in the catalogue.", fontsize=8, color=MUT)
    save(fig, "bermuda")


# ---------- the Bermuda Triangle under every test ----------
def fig_tests():
    B = R["bermuda"]; A = AR["Bermuda Triangle"]
    rows = [("Against traffic (AIS positions)", A["T"]), ("Against traffic (lanes index)", A["T_lanes"]), ("Since 1946 only", A["T_1946"]),
            ("Ships and boats only", A["T_ships"]), ("Its four neighbours, against traffic", {"ratio": B["neigh_x"], "lo": B["neigh_lo"], "hi": B["neigh_hi"], "o": B["neigh_o"], "e": B["neigh_e"], "flag": "higher"}),
            ("Against all recorded losses since 1800", A["L"]), ("Against recorded losses, war years left out", A["L_peace"]), ("Losses 2000 to 2025 against traffic", A["M"])]
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=BG); ax.set_facecolor(BG)
    for i, (lab, t) in enumerate(rows):
        y = len(rows) - i
        c = HOT if t["flag"].startswith("higher") else COOL if t["flag"].startswith("lower") else "#8A8F96"
        ax.plot([max(t["lo"], .05), min(t["hi"], 40)], [y, y], color=c, lw=3, solid_capstyle="round")
        ax.scatter([max(t["ratio"], .05)], [y], s=46, color=c, edgecolor="white", zorder=3)
        ax.text(50, y, f"{t['o']} v {t['e']:.1f}", va="center", fontsize=9, color=MUT)
    ax.set_yticks(range(len(rows), 0, -1)); ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.set_xscale("log"); ax.set_xlim(.08, 40); ax.axvline(1, color=FG, lw=1.2)
    ax.set_xticks([.1, .3, 1, 3, 10, 30]); ax.set_xticklabels(["0.1", "0.3", "1", "3", "10", "30"])
    ax.grid(axis="x", color=RULE); ax.set_axisbelow(True); spines(ax); ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.set_xlabel("observed ÷ expected, with 95% interval")
    ax.set_title("The Bermuda Triangle under every test", loc="left", fontproperties=DISPB, fontsize=15, x=-.62)
    fig.subplots_adjust(left=.42, right=.9, top=.88, bottom=.14); save(fig, "tests")


# ---------- the places that are worse ----------
def fig_worse():
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.6), facecolor=BG, gridspec_kw={"width_ratios": [1.25, 1]})
    for ax, (nm, lon0, lat0, lon1, lat1, title) in zip(axs, [("bass", 140, -45.5, 156, -31.5, "Bass Strait and the Tasman Sea"), ("lake", -92.5, 41.2, -82, 47.6, "Lake Michigan and Lake Superior")]):
        tr = Transformer.from_crs(4326, f"+proj=laea +lat_0={(lat0 + lat1) / 2} +lon_0={(lon0 + lon1) / 2} +datum=WGS84", always_xy=True)
        tri = Transformer.from_crs(f"+proj=laea +lat_0={(lat0 + lat1) / 2} +lon_0={(lon0 + lon1) / 2} +datum=WGS84", 4326, always_xy=True)
        xa, ya = tr.transform([lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1]); ext = (min(xa), max(xa), min(ya), max(ya))
        ax.set_facecolor(SEA)
        from shapely.geometry import shape as _sh
        G = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
        for f in G["features"]:
            g = _sh(f["geometry"])
            if not g.intersects(__import__("shapely.geometry", fromlist=["box"]).box(lon0 - 2, lat0 - 2, lon1 + 2, lat1 + 2)):
                continue
            for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
                r = np.array(poly.exterior.coords); x, y = tr.transform(r[:, 0], r[:, 1])
                ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=LAND, ec="white", lw=.5, zorder=1))
        if nm == "lake":
            S = jload(f"{DATA}/seas.json")
            for f in S["features"]:
                if f["properties"]["name"] in ("Rest of Lake Michigan", "Rest of the Great Lakes", "Michigan Triangle"):
                    cs = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
                    for poly in cs:
                        r = np.array(poly[0]); x, y = tr.transform(r[:, 0], r[:, 1])
                        ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=SEA, ec="none", zorder=1.5))
            triangle(ax, "Michigan Triangle", tr=tr, lw=1.6, col=FG)
        ax.imshow(traffic_img(ext, tri, 700, int(700 * (ext[3] - ext[2]) / (ext[1] - ext[0])), alpha_max=.55, blur=1.8, lo=2.8), extent=ext, zorder=2, interpolation="bilinear")
        D = P[P.lon.between(lon0, lon1) & P.lat.between(lat0, lat1)]
        dots(ax, D, tr=tr, s=46, z=5)
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(RULE)
        a = AR["Bass Strait and Tasman Sea" if nm == "bass" else "Rest of Lake Michigan"]["T"]
        ax.set_title(f"{title}\n{a['o']} disappearances against {a['e']:.2f} expected" if nm == "bass" else f"{title}\nLake Michigan: {a['o']} against {a['e']:.2f} expected", loc="left", fontsize=11, color=FG)
    fig.suptitle("Where the sea really is worse than its traffic", x=.01, ha="left", fontproperties=DISPB, fontsize=16)
    hs = [Line2D([], [], marker="o", ls="", ms=8, mfc=c, mec="white", label=k[0]) for k, c in zip(KINDS, KCOL)] + [Line2D([], [], color=FG, ls=(0, (5, 3)), label="Michigan Triangle")]
    fig.legend(handles=hs, loc="lower center", ncol=4, frameon=False, fontsize=10)
    fig.tight_layout(rect=(0, .06, 1, .95)); save(fig, "worse")


# ---------- header ----------
def header():
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
    ax = fig.add_axes([.47, .03, .52, .94]); ax.set_facecolor(SEA)
    x0, y0 = BT.transform(-86, 15); x1, y1 = BT.transform(-56, 38)
    bermuda_map(ax, (x0, x1, y0, y1), labels=False, s=70)
    for s in ax.spines.values():
        s.set_color(RULE)
    ax.set_xticks([]); ax.set_yticks([])
    B = R["bermuda"]
    fig.text(.04, .80, "Lost", fontproperties=DISP, fontsize=78, color=FG)
    fig.text(.236, .80, "at", fontproperties=DISP, fontsize=78, color=HOT)
    fig.text(.04, .645, "sea", fontproperties=DISP, fontsize=78, color=FG)
    fig.text(.04, .575, "Is the Bermuda Triangle worse\nthan its traffic would predict?", fontproperties=SERB, fontsize=19, color=FG, va="top")
    fig.text(.04, .27, f"{B['o']} v {B['e']:.1f}", fontproperties=DISP, fontsize=44, color=HOT)
    fig.text(.04, .245, "famous disappearances inside it, against\nthe number expected from its shipping", fontsize=12, color=MUT, va="top")
    fig.text(.04, .06, "maps.tristanhotham.com/lost-at-sea", fontsize=11, color=MUT)
    fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    fig_map(); fig_decades(); fig_forest(); fig_forest("M", "modern", "Recorded losses 2000 to 2025 against traffic, by sea")
    fig_funnel(); fig_bermuda(); fig_tests(); fig_worse(); header()
    from PIL import Image
    print(Image.open(os.path.join(ROOT, "header.png")).size, sorted(os.listdir(PAP)))
