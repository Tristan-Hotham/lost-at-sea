"""README.md, LICENSE and the Reddit post (reddit/post.md), with every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
B, C, D, M, W = R["bermuda"], R["cat"], R["dragon"], R["michigan"], R["worse"]
readme = f"""# Lost at sea: famous disappearances tested against shipping traffic

Is the Bermuda Triangle, or anywhere else, worse than its traffic would predict? {C['n']:,} famous disappearances from Wikipedia's lists of missing ships, missing aircraft and people who disappeared mysteriously at sea, plus the incidents told in the Bermuda, Dragon's and Michigan Triangle articles, placed at sea from their location text ({C['placed']:,} placed) and compared, sea by sea, with modern shipping (World Bank / IMF AIS ship density, 2015 to 2021) and with {R['losses']['n']:,} recorded wrecks that have a position. Interactive map with a traffic layer, the triangles, sea shading by observed against expected, a funnel plot and every number.

Interactive page: https://maps.tristanhotham.com/lost-at-sea/
Paper: https://doi.org/{{10.5281/zenodo.23856868}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/lost-at-sea/}}

## Headline results

- The Bermuda Triangle (Miami, Bermuda, San Juan) holds {B['o']} placed disappearances against {B['e']:.1f} expected from its {B['traffic_pct']:.2f}% share of AIS traffic: {B['x']:.1f} times, 95% interval {B['lo']:.1f} to {B['hi']:.1f} (beyond the 95% level, not the 99.8% funnel limit).
- Its four neighbours (US Atlantic coast, Caribbean, Gulf of Mexico, Grand Banks) run just as high: {B['neigh_o']} against {B['neigh_e']:.1f}, {B['neigh_x']:.1f} times. Within that group the Triangle's traffic share predicts {B['within_e']:.1f}; it has {B['o']}. Nothing singles it out.
- Only {B['famous_inside']} of the {B['famous_n']} incidents told in Wikipedia's Bermuda Triangle article lie inside the triangle (both at route midpoints); Flight 19, the Cotopaxi, the Marine Sulphur Queen and the Star Tiger are placed outside it.
- The Dragon's Triangle is as expected ({D['o']} against {D['e']:.1f}); the Michigan Triangle holds none of the placed incidents, though Lake Michigan as a whole is far above its modern traffic ({M['lake_o']} against {M['lake_e']:.2f}).
- Seas clearly worse than their traffic (beyond the 99.8% limit): {', '.join(w['name'] for w in W)}. Bass Strait and the Tasman Sea lead ({W[0]['o']} against {W[0]['e']:.2f}): colonial coastal traders in a stormy strait, carefully listed. Weather, shoals, historical traffic, aviation and reporting explain them.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; results, sea outlines embedded; other data loaded from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/disappearances.csv` | All {C['n']:,} incidents: id, name, kind, year, lat, lon, confidence (position given, near a named place, route midpoint, sea area only, not placed), how placed, location text, source lists, legend article, people named. CC BY-SA 4.0. |
| `data/losses.csv` | The {R['losses']['n']:,} positioned recorded wrecks used as the historical denominator (Wikipedia lists of shipwrecks and Wikidata), with cell and sea area. CC BY-SA 4.0. |
| `data/areas.csv` | Every sea area: traffic shares, observed, expected, ratio, 95% interval and verdict for each test. |
| `data/cells.csv` | Every 2 degree square with traffic, disappearances or losses: observed, expected and ratios. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/traffic.png` | AIS traffic rendered for the map (Web Mercator). |
| `data/points.json`, `losses_points.json`, `seas.json`, `cells.json`, `site.json`, `world.json`, `countries.json`, `cities.json` | Page data. |
| `code/` | Scripts, run in order (below), with the gazetteer and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Disappearances: the tables of the three Wikipedia lists ({C['rows_ships']}, {C['rows_aircraft']} and {C['rows_people']} rows, row spans filled, solved cases left out) and {C['rows_article']} incidents from the three triangle articles; duplicates merged on year plus a shared name word, or an aircraft and a person with the same full date, giving {C['n']:,} incidents.
- Placing: a hand-made gazetteer ({C['gaz_places']} places, {C['gaz_seas']} seas) and rules: coordinates or distance and bearing; "off" or "near" a place; the great-circle midpoint of a route up to 4,000 km; a named sea's representative point. Points on land are moved to the nearest sea within 75 km (200 km for routes). {C['fixes']} cases placed or corrected by hand, with notes in `code/01_disappearances.py`. {C['unplaced']} left out (whole oceans, land, routes across continents). Incidents placed only by a sea's name never count inside a triangle.
- Traffic: the 0.08 degree overview of the World Bank Global Shipping Traffic Density raster, which samples single pixels, so it is only used summed over 2 degree squares and named seas. A second "lanes" index (sampled pixels with at least {R['traffic']['lanes_min']:,} positions) checks the effect of uneven AIS reception.
- Tests: expected = total x share of traffic (or of recorded losses in the same years); exact Poisson 95% intervals; "clearly" means beyond the 99.8% funnel limit. Sensitivities: lanes index, since 1946, ships only, positions and places only, without war years.
- Caveats: famous, English-language disappearances only; rough placements; modern traffic is a proxy for past routes and does not cover aircraft; disappearances cluster, so intervals are a little too narrow; the sea outlines are simple shapes of my own.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, pyproj, rasterio, matplotlib, fontTools, BeautifulSoup and lxml, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read in place (paths in `code/common.py`): the Wikipedia articles and the AIS overview in `/home/claude/newdata/raw6/`, the cleaned wrecks of the world-shipwrecks study, and Natural Earth in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/lost/work` (set `LOSTTMP`).

```
python3 code/01_disappearances.py   # parse the lists and articles, geocode, merge: data/disappearances.csv
python3 code/02_traffic.py          # AIS traffic per 2 degree square and sea area, data/traffic.png
python3 code/03_losses.py           # recorded losses with positions: data/losses.csv
python3 code/04_analysis.py         # observed against expected, intervals, funnel: data/areas.csv, data/cells.csv
python3 code/05_results.py          # results.json and page data, checks on statements in words
python3 code/06_geo.py              # world outline, country and town names
python3 code/07_build_site.py       # index.html
python3 code/08_figures.py          # header, blog and paper figures
python3 code/09_paper.py            # paper PDF
python3 reddit/collage.py           # collage (labels checked against land, dots and each other)
python3 code/10_readme.py           # README, LICENSE, Reddit post
python3 code/11_release.py          # blog post, Zenodo files
```

## Sources and licences

- Wikipedia contributors, "List of missing ships", "List of missing aircraft", "List of people who disappeared mysteriously at sea", "Bermuda Triangle", "Devil's Sea" and "Lake Michigan Triangle" (https://en.wikipedia.org/), retrieved 2026, CC BY-SA 4.0. `data/disappearances.csv` is derived from them and shared under CC BY-SA 4.0.
- Wikipedia contributors, Lists of shipwrecks (https://en.wikipedia.org/wiki/Lists_of_shipwrecks), CC BY-SA 4.0, and Wikidata (https://www.wikidata.org/), CC0, as cleaned in the study "Shipwrecks of the world" (https://maps.tristanhotham.com/world-shipwrecks/). `data/losses.csv` is shared under CC BY-SA 4.0.
- World Bank, Global Shipping Traffic Density (https://datacatalog.worldbank.org/search/dataset/0037580), produced by the IMF and World Bank from AIS data, January 2015 to February 2021 (see Cerdeiro, Komaromi, Liu and Saeed 2020, IMF Working Paper 20/57), CC BY 4.0. Used as sums over squares and seas and as a rendered image.
- Natural Earth land, countries and populated places (https://www.naturalearthdata.com/), public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Lost at sea: famous disappearances tested against shipping traffic. Zenodo. https://doi.org/{{10.5281/zenodo.23856868}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
lic = """Code (everything in code/ and reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data (data/, release/, reddit/*.png, header.png, index.html text): Creative Commons Attribution 4.0
International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/. Attribution: Tristan Hotham (2026).
Exception: data/disappearances.csv and data/losses.csv (and the page data derived from them: data/points.json,
data/losses_points.json) are derived from Wikipedia (Wikipedia contributors, CC BY-SA 4.0) and are shared under CC BY-SA 4.0,
https://creativecommons.org/licenses/by-sa/4.0/.

Third-party data: Wikipedia text is CC BY-SA 4.0. Wikidata content is CC0. The World Bank Global Shipping Traffic Density is
CC BY 4.0 (World Bank; IMF and World Bank, from AIS data); it is used here as sums and a rendered image (data/traffic.png).
Natural Earth is public domain.
"""
post = f"""## Title

[OC] Is the Bermuda Triangle worse than its traffic would predict? {B['o']} famous disappearances inside it against {B['e']:.1f} expected, but its neighbours run just as high

## Body

I took Wikipedia's lists of missing ships, missing aircraft and people who disappeared mysteriously at sea, plus the incidents in the Bermuda, Dragon's and Michigan Triangle articles, merged duplicates and placed {C['placed']} of the {C['n']} incidents at sea from their location text. Then I compared every sea with its share of modern shipping (World Bank / IMF AIS ship density, 2015 to 2021). The Bermuda Triangle has {B['x']:.1f} times the disappearances its traffic predicts (95% interval {B['lo']:.1f} to {B['hi']:.1f}), but the US Atlantic coast, Caribbean, Gulf of Mexico and Grand Banks together are {B['neigh_x']:.1f} times, so within its region it has exactly its share ({B['o']} v {B['within_e']:.1f}). Only {B['famous_inside']} of the {B['famous_n']} incidents on its Wikipedia page are actually inside the triangle. The seas that really stand out are Bass Strait and the Tasman Sea ({W[0]['o']} v {W[0]['e']:.2f}: colonial schooners in a stormy strait) and the Great Lakes. Big caveats: these are famous, English-language disappearances, placements are rough, and modern AIS traffic is only a proxy for where ships and planes went decades ago. Interactive map with a funnel plot: https://maps.tristanhotham.com/lost-at-sea/

## Source comment

Sources: Wikipedia contributors, List of missing ships, List of missing aircraft, List of people who disappeared mysteriously at sea, and the Bermuda Triangle, Devil's Sea and Lake Michigan Triangle articles (CC BY-SA 4.0); World Bank, Global Shipping Traffic Density (IMF and World Bank, AIS data 2015 to 2021, CC BY 4.0); recorded wrecks from Wikipedia's lists of shipwrecks and Wikidata; Natural Earth. Expected counts = total x each sea's share of traffic; exact Poisson 95% intervals; "clearly worse" = beyond the 99.8% funnel limit. Results hold with a second traffic index that is less sensitive to uneven AIS reception. Map labels were placed by a script that checks they sit on open sea and never cover a data point.

Tools: Python (pandas, scipy, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/lost-at-sea/
Paper: https://doi.org/{{10.5281/zenodo.23856868}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/lost-at-sea/}}
"""
for txt in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in txt.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w").write(readme)
open(os.path.join(ROOT, "LICENSE"), "w").write(lic)
open(os.path.join(ROOT, "reddit", "post.md"), "w").write(post)
print("README", len(readme.split()), "words; post title:", post.splitlines()[2])
