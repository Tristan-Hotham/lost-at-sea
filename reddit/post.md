## Title

[OC] Is the Bermuda Triangle worse than its traffic would predict? 8 famous disappearances inside it against 2.8 expected, but its neighbours run just as high

## Body

I took Wikipedia's lists of missing ships, missing aircraft and people who disappeared mysteriously at sea, plus the incidents in the Bermuda, Dragon's and Michigan Triangle articles, merged duplicates and placed 472 of the 673 incidents at sea from their location text. Then I compared every sea with its share of modern shipping (World Bank / IMF AIS ship density, 2015 to 2021). The Bermuda Triangle has 2.9 times the disappearances its traffic predicts (95% interval 1.2 to 5.6), but the US Atlantic coast, Caribbean, Gulf of Mexico and Grand Banks together are 2.7 times, so within its region it has exactly its share (8 v 7.7). Only 2 of the 14 incidents on its Wikipedia page are actually inside the triangle. The seas that really stand out are Bass Strait and the Tasman Sea (48 v 0.18: colonial schooners in a stormy strait) and the Great Lakes. Big caveats: these are famous, English-language disappearances, placements are rough, and modern AIS traffic is only a proxy for where ships and planes went decades ago. Interactive map with a funnel plot: https://maps.tristanhotham.com/lost-at-sea/

## Source comment

Sources: Wikipedia contributors, List of missing ships, List of missing aircraft, List of people who disappeared mysteriously at sea, and the Bermuda Triangle, Devil's Sea and Lake Michigan Triangle articles (CC BY-SA 4.0); World Bank, Global Shipping Traffic Density (IMF and World Bank, AIS data 2015 to 2021, CC BY 4.0); recorded wrecks from Wikipedia's lists of shipwrecks and Wikidata; Natural Earth. Expected counts = total x each sea's share of traffic; exact Poisson 95% intervals; "clearly worse" = beyond the 99.8% funnel limit. Results hold with a second traffic index that is less sensitive to uneven AIS reception. Map labels were placed by a script that checks they sit on open sea and never cover a data point.

Tools: Python (pandas, scipy, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/lost-at-sea/
Paper: https://doi.org/10.5281/zenodo.23856868
Blog post: https://blog.tristanhotham.com/2026/10/31/lost-at-sea/
