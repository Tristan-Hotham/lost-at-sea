"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines, the AIS traffic as an image in any projection, and the sea
outlines shaded by observed against expected."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
import pandas as pd
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#636A72", "#E2DED3", "#DDD8CC", "#EEF2F3"
HOT, COOL, GOLD, INK = "#B3202A", "#2F7FB8", "#C9A227", "#1F3A5F"
KCOL = [k[1] for k in KINDS]; CCOL = [c[1] for c in CONF]
EE = Transformer.from_crs(4326, 8857, always_xy=True)
EEi = Transformer.from_crs(8857, 4326, always_xy=True)
W = jload(f"{DATA}/world.json")
RAMP = [(47, 127, 184), (143, 181, 207), (221, 214, 198), (233, 160, 104), (205, 74, 52), (150, 22, 36), (92, 10, 30)]
RSTOP = [-1.5, -0.6, 0, 0.45, 1.0, 1.7, 2.6]


def rcol(r):
    """Diverging colour for an observed/expected ratio (same scale as the page)."""
    if r is None:
        return "#DDD6C6"
    t = max(RSTOP[0], min(RSTOP[-1], math.log10(max(r, .02))))
    i = 0
    while i < len(RSTOP) - 2 and t > RSTOP[i + 1]:
        i += 1
    u = (t - RSTOP[i]) / (RSTOP[i + 1] - RSTOP[i])
    return tuple((RAMP[i][j] + (RAMP[i + 1][j] - RAMP[i][j]) * u) / 255 for j in range(3))


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = [np.array(r) for f in W["features"] for r in rings(f["geometry"])]
WORLD_EXT = (-16.6e6, 17.0e6, -6.9e6, 8.4e6)


def world(ax, tr=EE, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1, clip=None):
    for ring in SHAPES:
        if clip and (ring[:, 0].max() < clip[0] or ring[:, 0].min() > clip[2] or ring[:, 1].max() < clip[1] or ring[:, 1].min() > clip[3]):
            continue
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def proj(lon, lat, tr=EE):
    return tr.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


_L = {}


def _logtraffic(blur=1.1):
    """Log AIS density on the 0.08 degree grid; the sampled overview is spread with a maximum filter and a gaussian
    blur so that lanes read as lanes (more blur for close-up maps)."""
    if blur not in _L:
        A = np.frombuffer(gzip.open(f"{RAW6}/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz").read(), dtype="<i4").reshape(2125, 4501).astype(np.float64)
        from scipy.ndimage import gaussian_filter, maximum_filter
        _L[blur] = gaussian_filter(maximum_filter(np.log10(1 + A), size=3), blur)
    return _L[blur]


def traffic_img(ext, tr_inv, px_w, px_h, alpha_max=.9, blur=1.1, lo=2.2):
    """RGBA image of log AIS traffic for a projected extent (x0, x1, y0, y1), sampling the 0.08 degree raster."""
    L = _logtraffic(blur)
    xs = np.linspace(ext[0], ext[1], px_w); ys = np.linspace(ext[3], ext[2], px_h)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = tr_inv.transform(X.ravel(), Y.ravel())
    lon = np.asarray(lon); lat = np.asarray(lat)
    ok = np.isfinite(lon) & np.isfinite(lat) & (np.abs(lat) < 85)
    v = np.zeros(lon.size)
    r = ((85 - lat[ok]) / (170 / 2125)).astype(int).clip(0, 2124); c = ((lon[ok] + 180) / (360 / 4501)).astype(int).clip(0, 4500)
    v[ok] = L[r, c]
    t = np.clip((v - lo) / (7.2 - lo), 0, 1).reshape(px_h, px_w)
    ramp = np.array([[160, 205, 218], [80, 150, 185], [32, 96, 148], [16, 46, 92]], float)
    s = t * (len(ramp) - 1); a0 = np.minimum(len(ramp) - 2, s.astype(int)); u = (s - a0)[..., None]
    rgb = (ramp[a0] * (1 - u) + ramp[a0 + 1] * u) / 255
    a = np.where(t > 0, (.18 + .82 * t ** .9) * alpha_max, 0)
    return np.dstack([rgb, a])


def densify(ring, step=.5):
    """Add points along long straight edges (in degrees) so they bend correctly when projected."""
    out = []
    for i in range(len(ring) - 1):
        a, b = ring[i], ring[i + 1]
        n = max(1, int(np.hypot(*(b - a)) / step))
        out.extend(a + (b - a) * t for t in np.arange(n) / n)
    out.append(ring[-1])
    return np.array(out)


def seas_shade(ax, key="T", tr=EE, z=2, alpha=.62, pale=.22, ec="none", only=None):
    R = jload(f"{DATA}/results.json"); S = jload(f"{DATA}/seas.json")
    for f in S["features"]:
        a = R["areas"][f["properties"]["i"]]
        if only and a["name"] not in only:
            continue
        t = a[key]
        if not t:
            continue
        cs = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
        for poly in cs:
            ring = densify(np.array(poly[0]))
            x, y = tr.transform(ring[:, 0], ring[:, 1])
            ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=rcol(t["ratio"]), ec=ec, lw=.4, alpha=pale if t["flag"] == "as expected" else alpha, zorder=z))


def triangle(ax, nm, tr=EE, lw=1.6, z=6, col=None):
    vs = TRIANGLES[nm]["verts"]
    xs, ys = [], []
    for i in range(3):
        a, b = vs[i], vs[(i + 1) % 3]
        for t in np.linspace(0, 1, 60):
            xs.append(a[0] + (b[0] - a[0]) * t); ys.append(a[1] + (b[1] - a[1]) * t)
    x, y = tr.transform(np.array(xs), np.array(ys))
    ax.plot(np.r_[x, x[0]], np.r_[y, y[0]], color=col or TRIANGLES[nm]["col"], lw=lw, ls=(0, (5, 3)), zorder=z)


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def halo(t, w=3, c="white"):
    import matplotlib.patheffects as pe
    t.set_path_effects([pe.withStroke(linewidth=w, foreground=c)])
    return t
