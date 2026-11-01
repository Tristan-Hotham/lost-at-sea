"""Modern shipping traffic from the World Bank / IMF AIS ship density (2015 to 2021), as a traffic index per 2 degree
cell and per named sea area, plus a PNG overlay for the map.

The input is the 0.08 degree overview of the global raster, which samples single full-resolution pixels, so a value
says little on its own; summed over the 625 or so samples in a 2 degree cell (or the thousands in a sea area) it is a
fair index of how much AIS-tracked traffic passes there. The index is expressed as a share of the world total.
Outputs (WORK): traffic.npz (cells: sum, samples, non-zero samples; areas: sum), and data/traffic.png (Web Mercator,
85.05 S to 85.05 N, for a Leaflet image overlay)."""
import numpy as np
from matplotlib.path import Path
from PIL import Image
from common import *
from areas import AREAS, NAMES

H, W = 2125, 4501
A = np.frombuffer(gzip.open(f"{RAW6}/shipdensity/shipdensity_global_ovr_4501x2125_int32le.bin.gz").read(), dtype="<i4").reshape(H, W).astype(np.float64)
assert A.min() >= 0
dx, dy = 360 / W, 170 / H
lon = -180 + (np.arange(W) + .5) * dx
lat = 85 - (np.arange(H) + .5) * dy

# ---- 2 degree cells: rows from 85N southwards (lat index), columns from 180W eastwards
NR, NC = int(170 / CELL), int(360 / CELL)
ri = np.minimum(((85 - lat) // CELL).astype(int), NR - 1)
ci = np.minimum(((lon + 180) // CELL).astype(int), NC - 1)
RI, CI = np.meshgrid(ri, ci, indexing="ij")
flat = (RI * NC + CI).ravel()
csum = np.bincount(flat, weights=A.ravel(), minlength=NR * NC).reshape(NR, NC)
cnt = np.bincount(flat, minlength=NR * NC).reshape(NR, NC)
cnz = np.bincount(flat, weights=(A.ravel() > 0), minlength=NR * NC).reshape(NR, NC)

# ---- named areas (pixel by pixel, first match wins)
nz = np.nonzero(A > 0)
pts = np.column_stack([lon[nz[1]], lat[nz[0]]])
vals = A[nz]
owner = np.full(len(vals), len(AREAS))
free = np.ones(len(vals), bool)
for k, a in enumerate(AREAS):
    inside = Path(a[3] + [a[3][0]]).contains_points(pts) & free
    owner[inside] = k; free &= ~inside
asum = np.bincount(owner, weights=vals, minlength=len(NAMES))
tot = A.sum()
assert abs(asum.sum() - tot) / tot < 1e-9
# "lanes" index: sampled pixels with at least 1,000 AIS positions (a sensitivity check, less driven by receiver density)
LANE_MIN = 1000
alanes = np.bincount(owner, weights=(vals >= LANE_MIN), minlength=len(NAMES))
clanes = np.bincount(flat, weights=(A.ravel() >= LANE_MIN), minlength=NR * NC).reshape(NR, NC)
jsave({"min_positions": LANE_MIN, "share": [float(x / alanes.sum()) for x in alanes], "n": int(alanes.sum())}, f"{WORK}/lanes.json")
np.savez_compressed(f"{WORK}/traffic.npz", csum=csum, cnt=cnt, cnz=cnz, asum=asum, tot=tot, clanes=clanes)
for n, v in sorted(zip(NAMES, asum), key=lambda x: -x[1]):
    print(f"{n:38s} {100 * v / tot:6.2f}%")

# ---- overlay PNG in Web Mercator: log density, lightly smoothed so the sampled lanes read as lanes
L = np.log10(1 + A)
try:
    from scipy.ndimage import gaussian_filter, maximum_filter
    L = gaussian_filter(maximum_filter(L, size=3), 1.3)
except ImportError:
    pass
S = 2048
MAXLAT = 85.0511
ys = np.arange(S) + .5
mlat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * ys / S))))
mlon = -180 + (np.arange(S) + .5) * 360 / S
rr = np.clip(((85 - mlat) / dy).astype(int), 0, H - 1)
cc = np.clip(((mlon + 180) / dx).astype(int), 0, W - 1)
V = L[rr][:, cc]
V[np.abs(mlat) > 85] = 0
t = np.clip((V - 2.0) / (7.3 - 2.0), 0, 1)               # 10^2 to 10^7.3 AIS positions per sampled pixel
ramp = np.array([[148, 201, 214], [62, 145, 181], [32, 96, 148], [22, 52, 102], [12, 26, 60]], float)
s = t * (len(ramp) - 1); a0 = np.minimum(len(ramp) - 2, s.astype(int)); u = (s - a0)[..., None]
rgb = ramp[a0] * (1 - u) + ramp[a0 + 1] * u
alpha = np.where(V > 0.6, 40 + 215 * t ** .9, 0)
img = np.dstack([rgb, alpha]).astype(np.uint8)
Image.fromarray(img, "RGBA").save(f"{DATA}/traffic.png", optimize=True)
print("traffic.png", os.path.getsize(f"{DATA}/traffic.png") // 1024, "KB")
