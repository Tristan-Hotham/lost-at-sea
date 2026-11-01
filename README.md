# Lost at sea: famous disappearances tested against shipping traffic

Is the Bermuda Triangle, or anywhere else, worse than its traffic would predict? 673 famous disappearances from Wikipedia's lists of missing ships, missing aircraft and people who disappeared mysteriously at sea, plus the incidents told in the Bermuda, Dragon's and Michigan Triangle articles, placed at sea from their location text (472 placed) and compared, sea by sea, with modern shipping (World Bank / IMF AIS ship density, 2015 to 2021) and with 17,224 recorded wrecks that have a position. Interactive map with a traffic layer, the triangles, sea shading by observed against expected, a funnel plot and every number.

Interactive page: https://maps.tristanhotham.com/lost-at-sea/
Paper: https://doi.org/10.5281/zenodo.23856868
Blog post: https://blog.tristanhotham.com/2026/10/31/lost-at-sea/

## Headline results

- The Bermuda Triangle (Miami, Bermuda, San Juan) holds 8 placed disappearances against 2.8 expected from its 0.59% share of AIS traffic: 2.9 times, 95% interval 1.2 to 5.6 (beyond the 95% level, not the 99.8% funnel limit).
- Its four neighbours (US Atlantic coast, Caribbean, Gulf of Mexico, Grand Banks) run just as high: 80 against 29.1, 2.7 times. Within that group the Triangle's traffic share predicts 7.7; it has 8. Nothing singles it out.
- Only 2 of the 14 incidents told in Wikipedia's Bermuda Triangle article lie inside the triangle (both at route midpoints); Flight 19, the Cotopaxi, the Marine Sulphur Queen and the Star Tiger are placed outside it.
- The Dragon's Triangle is as expected (7 against 6.3); the Michigan Triangle holds none of the placed incidents, though Lake Michigan as a whole is far above its modern traffic (16 against 0.23).
- Seas clearly worse than their traffic (beyond the 99.8% limit): Bass Strait and Tasman Sea, Rest of Lake Michigan, Rest of the Great Lakes, US Atlantic coast, Caribbean Sea, English Channel, Newfoundland and the Grand Banks. Bass Strait and the Tasman Sea lead (48 against 0.18): colonial coastal traders in a stormy strait, carefully listed. Weather, shoals, historical traffic, aviation and reporting explain them.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; results, sea outlines embedded; other data loaded from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/disappearances.csv` | All 673 incidents: id, name, kind, year, lat, lon, confidence (position given, near a named place, route midpoint, sea area only, not placed), how placed, location text, source lists, legend article, people named. CC BY-SA 4.0. |
| `data/losses.csv` | The 17,224 positioned recorded wrecks used as the historical denominator (Wikipedia lists of shipwrecks and Wikidata), with cell and sea area. CC BY-SA 4.0. |
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

- Disappearances: the tables of the three Wikipedia lists (201, 289 and 223 rows, row spans filled, solved cases left out) and 21 incidents from the three triangle articles; duplicates merged on year plus a shared name word, or an aircraft and a person with the same full date, giving 673 incidents.
- Placing: a hand-made gazetteer (359 places, 58 seas) and rules: coordinates or distance and bearing; "off" or "near" a place; the great-circle midpoint of a route up to 4,000 km; a named sea's representative point. Points on land are moved to the nearest sea within 75 km (200 km for routes). 134 cases placed or corrected by hand, with notes in `code/01_disappearances.py`. 201 left out (whole oceans, land, routes across continents). Incidents placed only by a sea's name never count inside a triangle.
- Traffic: the 0.08 degree overview of the World Bank Global Shipping Traffic Density raster, which samples single pixels, so it is only used summed over 2 degree squares and named seas. A second "lanes" index (sampled pixels with at least 1,000 positions) checks the effect of uneven AIS reception.
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

Hotham, T. (2026) Lost at sea: famous disappearances tested against shipping traffic. Zenodo. https://doi.org/10.5281/zenodo.23856868

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
