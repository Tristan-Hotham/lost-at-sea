"""Named sea areas for the comparison (lon, lat polygons). Areas are tested in this order and a point or traffic pixel
belongs to the first area that contains it, so the areas never overlap: the three legendary triangles first, then the
smaller seas, then the large ones, and "Rest of the world's seas" for everything else. The outlines are deliberately
simple (they may cut across land, which holds neither traffic nor losses); they follow the usual extents of each sea
only roughly."""
from common import TRIANGLES, point_in_poly

box = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
tri = lambda nm: [(v[0], v[1]) for v in TRIANGLES[nm]["verts"]]

# (name, short label, region, polygon)
AREAS = [
    ("Bermuda Triangle", "Bermuda Tri.", "legend", tri("Bermuda Triangle")),
    ("Dragon's Triangle", "Dragon's Tri.", "legend", tri("Dragon's Triangle")),
    ("Michigan Triangle", "Michigan Tri.", "legend", tri("Michigan Triangle")),
    ("Rest of Lake Michigan", "L. Michigan", "lake", box(-88.2, 41.5, -84.7, 46.2)),
    ("Rest of the Great Lakes", "Great Lakes", "lake", box(-92.5, 41.0, -75.5, 49.2)),
    ("English Channel", "Channel", "europe", [(-5.8, 48.3), (-5.8, 50.1), (-5.0, 50.3), (-1.0, 50.85), (1.0, 51.15), (1.95, 51.2), (1.95, 50.7), (-1.0, 49.3), (-4.5, 48.3)]),
    ("North Sea", "North Sea", "europe", [(-4.0, 51.0), (2.0, 51.2), (9.5, 53.0), (9.5, 57.5), (11.0, 58.5), (6.0, 61.5), (-4.0, 61.5)]),
    ("Baltic Sea", "Baltic", "europe", [(9.5, 53.0), (30.5, 53.0), (30.5, 66.0), (9.5, 66.0), (9.5, 57.5), (11.0, 58.5), (12.5, 57.0)]),
    ("Irish and Celtic Seas", "Irish Sea", "europe", box(-11.0, 49.5, -2.5, 56.0)),
    ("Bay of Biscay", "Biscay", "europe", box(-10.0, 43.2, -1.0, 48.4)),
    ("Black Sea", "Black Sea", "europe", box(27.3, 40.8, 42.0, 47.5)),
    ("Mediterranean Sea", "Mediterranean", "europe", box(-5.6, 30.0, 37.0, 45.9)),
    ("Gulf of Mexico", "Gulf of Mexico", "americas", [(-98.0, 18.0), (-89.0, 18.0), (-87.0, 21.5), (-84.9, 21.9), (-81.0, 23.0), (-81.0, 31.0), (-98.0, 31.0)]),
    ("Caribbean Sea", "Caribbean", "americas", [(-89.0, 8.0), (-60.0, 8.0), (-60.0, 18.5), (-64.5, 18.5), (-68.0, 18.3), (-74.0, 18.5), (-74.5, 20.0), (-80.0, 23.0), (-84.9, 21.9), (-87.0, 21.5), (-89.0, 18.0)]),
    ("US Atlantic coast", "US Atlantic", "americas", [(-82.0, 25.0), (-80.19, 25.76), (-73.0, 29.0), (-66.0, 36.0), (-62.0, 41.0), (-66.0, 45.5), (-82.0, 45.5)]),
    ("Newfoundland and the Grand Banks", "Grand Banks", "americas", box(-66.0, 41.0, -45.0, 56.0)),
    ("Gulf of Alaska", "Gulf of Alaska", "americas", box(-160.0, 52.0, -130.0, 61.5)),
    ("North Atlantic, open ocean", "N. Atlantic", "ocean", box(-82.0, 0.0, -5.0, 66.0)),
    ("South China Sea", "S. China Sea", "asia", [(99.0, 0.0), (105.0, -3.0), (109.0, -3.0), (117.0, 4.0), (120.0, 6.0), (120.5, 13.0), (122.0, 18.5), (121.0, 22.5), (117.0, 23.6), (108.0, 22.5), (105.0, 15.0), (101.0, 7.0)]),
    ("East China and Yellow Seas", "E. China Sea", "asia", [(117.0, 23.6), (121.0, 22.5), (122.0, 24.0), (127.0, 26.0), (131.0, 31.0), (129.0, 34.5), (126.5, 41.0), (117.0, 41.0)]),
    ("Sea of Japan", "Sea of Japan", "asia", [(129.0, 34.5), (131.0, 33.8), (140.0, 37.5), (141.5, 41.5), (142.0, 46.0), (141.0, 52.0), (136.0, 46.0), (129.0, 38.0)]),
    ("Indonesian seas", "Indonesian seas", "asia", [(105.0, -3.0), (109.0, -3.0), (117.0, 4.0), (120.0, 6.0), (127.0, 6.0), (135.0, 0.0), (135.0, -11.0), (105.0, -9.0)]),
    ("Malacca Strait and Andaman Sea", "Malacca", "asia", [(92.0, 16.5), (99.0, 16.5), (101.0, 7.0), (99.0, 0.0), (105.0, -3.0), (95.0, 6.0), (92.0, 8.0)]),
    ("Bay of Bengal", "Bay of Bengal", "asia", box(78.0, 5.0, 95.0, 23.0)),
    ("Arabian Sea and the Gulfs", "Arabian Sea", "asia", box(48.0, 5.0, 78.0, 30.5)),
    ("Bass Strait and Tasman Sea", "Tasman Sea", "oceania", box(140.0, -48.0, 175.0, -28.0)),
]
REST = "Rest of the world's seas"
NAMES = [a[0] for a in AREAS] + [REST]


def area_of(lon, lat):
    for i, a in enumerate(AREAS):
        if point_in_poly(lon, lat, a[3]):
            return i
    return len(AREAS)
