"""Hand-made gazetteer for geocoding the location text of the Wikipedia lists (lon, lat in degrees).

PLACES: ports, capes, islands and coasts. Coastal places are given a point just offshore where it matters, so that
"off X" lands at sea. SEAS: named seas, straits, gulfs and bays, with a representative point inside them (used only
with the confidence "Sea area only"). OCEANS: whole oceans; an incident placed only by an ocean is left unplaced.
Coordinates are approximate (to about 0.1 degree), from general knowledge of the places; they are only used to put an
incident in a 2 degree cell or a named sea area."""

PLACES = {
    # North America, Atlantic coast and Caribbean
    "miami": (-80.10, 25.77), "jupiter inlet": (-80.00, 26.95), "coast of ireland": (-10.30, 51.80), "coast of turkey": (27.50, 36.80), "east coast of florida": (-79.80, 27.50), "coast of florida": (-79.80, 27.50), "fort lauderdale": (-80.08, 26.12), "ft lauderdale": (-80.08, 26.12), "palm beach": (-80.02, 26.70),
    "st augustine": (-81.25, 29.89), "st. augustine": (-81.25, 29.89), "clearwater": (-82.90, 27.97), "bimini": (-79.30, 25.73),
    "nassau": (-77.35, 25.08), "the bahamas": (-77.40, 24.80), "bahamas": (-77.40, 24.80), "turks and caicos": (-71.80, 21.80),
    "havana": (-82.36, 23.17), "cuba": (-79.50, 21.00), "camaguey": (-77.90, 21.40), "jamaica": (-77.30, 17.80), "kingston, jamaica": (-76.80, 17.90),
    "kingston": (-76.80, 17.90), "haiti": (-72.70, 19.90), "port-au-prince": (-72.40, 18.60), "port au prince": (-72.40, 18.60), "santo domingo": (-69.90, 18.40),
    "dominican republic": (-69.60, 18.30), "puerto rico": (-66.20, 18.60), "san juan": (-66.10, 18.50), "mayaguez": (-67.20, 18.20), "mona channel": (-67.80, 18.20),
    "virgin islands": (-64.80, 18.40), "united states virgin islands": (-64.80, 18.30), "saint john": (-64.75, 18.30), "barbados": (-59.60, 13.10),
    "martinique": (-61.10, 14.60), "guadeloupe": (-61.60, 16.20), "sint eustatius": (-63.00, 17.50), "trinidad": (-61.40, 10.70), "curacao": (-69.00, 12.15),
    "willemstad": (-68.95, 12.10), "aruba": (-70.00, 12.55), "bocas del toro": (-82.20, 9.40), "cristobal": (-79.90, 9.45), "colon": (-79.90, 9.45),
    "bermuda": (-64.78, 32.30), "cape hatteras": (-75.40, 35.20), "diamond shoals": (-75.40, 35.15), "outer banks": (-75.50, 35.60), "cape lookout": (-76.50, 34.55),
    "norfolk, virginia": (-76.00, 36.95), "norfolk": (-76.00, 36.95), "chesapeake bay": (-76.20, 37.80), "baltimore": (-76.30, 37.00), "philadelphia": (-74.90, 38.80),
    "newcastle, delaware": (-74.90, 38.80), "atlantic city": (-74.30, 39.35), "new york city": (-73.80, 40.40), "new york": (-73.80, 40.40), "long island": (-72.80, 40.70),
    "staten island": (-74.05, 40.50), "boston": (-70.70, 42.35), "portland, maine": (-70.10, 43.60), "maine": (-68.50, 43.80), "martha's vineyard": (-70.60, 41.30),
    "vineyard haven": (-70.60, 41.30), "rhode island": (-71.40, 41.40), "brunswick, ga": (-81.30, 31.10), "georgetown, south carolina": (-79.15, 33.30),
    "south carolina": (-79.00, 32.80), "st. mary's, georgia": (-81.30, 30.70), "charleston": (-79.80, 32.70), "maryland": (-75.00, 38.30),
    "halifax": (-63.50, 44.55), "sable island": (-60.00, 43.95), "nova scotia": (-63.00, 44.20), "yarmouth, nova scotia": (-66.20, 43.80), "cape breton": (-60.00, 46.20),
    "newfoundland": (-52.50, 47.00), "cape race": (-53.00, 46.60), "st. john's": (-52.60, 47.55), "st john's": (-52.60, 47.55), "st. anthony": (-55.50, 51.40),
    "labrador": (-57.00, 54.50), "saint john, new brunswick": (-66.05, 45.20), "quebec city": (-70.90, 47.00), "montreal": (-70.90, 47.00), "cape farewell": (-43.90, 59.60),
    "greenland": (-43.00, 59.00), "eastern passage": (-63.50, 44.60),
    # Gulf of Mexico and Pacific coast of the Americas
    "sabine pass": (-93.85, 29.60), "port arthur, texas": (-93.85, 29.60), "baja california": (-116.50, 30.00),
    "san diego": (-117.40, 32.60), "carlsbad": (-117.40, 33.10), "los angeles": (-118.40, 33.70), "santa monica": (-118.60, 33.95), "santa monica bay": (-118.60, 33.90),
    "santa barbara": (-119.70, 34.30), "san francisco": (-122.65, 37.75), "san francisco bay": (-122.40, 37.75), "oakland": (-122.65, 37.75),
    "farallon islands": (-123.00, 37.70), "moffett": (-122.65, 37.40), "salina cruz": (-95.20, 16.10), "costa azul": (-93.50, 15.60), "valparaiso": (-71.70, -33.00),
    "iquique": (-70.20, -20.20), "cape horn": (-67.30, -56.10), "buenos aires": (-56.50, -35.20), "montevideo": (-56.00, -35.00), "falkland islands": (-58.50, -51.90),
    "east falkland": (-58.50, -51.90), "natal": (-35.10, -5.70), "fernando de noronha": (-32.40, -3.85), "saint peter and saint paul archipelago": (-29.35, 0.92),
    "pernambuco": (-34.80, -8.10), "british guiana": (-58.10, 6.90), "maroni river": (-53.90, 5.85), 
    # Alaska and the north Pacific
    "cape spencer": (-136.65, 58.15), "juneau": (-134.60, 58.20), "anchorage": (-150.50, 60.50), "kodiak": (-152.40, 57.70), "woody island": (-152.40, 57.80),
    "yakutat": (-139.90, 59.40), "umnak island": (-168.30, 53.40), "adak": (-176.70, 51.80), "shemya": (174.10, 52.70), "hecate strait": (-130.80, 53.30),
    "graham island": (-131.80, 53.60), "portage bay": (-122.30, 47.65),
    "hawaii": (-157.80, 21.10), "honolulu": (-157.90, 21.20), "molokai": (-157.00, 21.30), "lanai": (-156.90, 20.70), "oahu": (-158.00, 21.40),
    "howland island": (-176.60, 0.80), "midway island": (-177.37, 28.20), "midway": (-177.37, 28.20), "palmyra": (-162.10, 5.90), "palmyra atoll": (-162.10, 5.90),
    "palmyra island atoll": (-162.10, 5.90), "kwajalein": (167.70, 9.20), "guam": (144.60, 13.40), "mariana islands": (145.70, 15.20), "maug islands": (145.22, 20.03),
    "iwo jima": (141.30, 24.70), "chuuk": (151.80, 7.40), "chuuk state": (151.80, 7.40), "kiribati": (-157.40, 1.90), "tahiti": (-149.50, -17.60),
    "nuku'alofa": (-175.20, -21.10), "pago pago": (-170.70, -14.30), "vanua levu": (179.30, -16.20), "fiji": (178.50, -17.50),
    # East and south-east Asia
    "tokyo": (140.00, 35.20), "aomori": (141.50, 41.30), "yakushima": (130.50, 30.30), "ryukyu islands": (127.50, 26.50), "okinawa": (127.70, 26.30),
    "kadena": (127.70, 26.30), "colnett strait": (130.00, 30.00), "tokara": (129.70, 29.60), "satsuma": (130.20, 31.30), "mikura-jima": (139.60, 33.87),
    "myojin-sho": (140.02, 31.92), "miyake-jima": (139.50, 34.08), "taiwan": (121.80, 25.30), "luzon strait": (121.00, 20.50), "manila": (120.80, 14.50),
    "lingayen gulf": (120.25, 16.30), "philippines": (125.50, 12.00), "davao": (125.70, 6.90), "tanon strait": (123.40, 10.30), "mindoro": (121.00, 13.00),
    "malalang bay": (122.00, 14.00), "paracel islands": (112.00, 16.50), "hong kong": (114.20, 22.20), "hanoi": (107.00, 20.50), "singapore": (103.85, 1.20),
    "singapore strait": (104.00, 1.20), "sisters' islands": (103.83, 1.21), "malay peninsula": (103.80, 3.50), "sulawesi": (122.50, -1.00), "kema": (125.10, 1.40),
    "babo": (133.40, -2.60), "madura island": (113.30, -7.20), "java": (107.00, -6.40), "sunda strait": (105.70, -6.20), "banyuwangi": (114.40, -8.20),
    "aluta island": (126.00, -2.00), "nicobar islands": (93.50, 8.00), "gulf of martaban": (97.00, 15.80),
    # South Asia and the Middle East
    "madras": (80.40, 13.10), "cuddalore": (79.90, 11.70), "margao": (73.80, 15.30), "margoa": (73.80, 15.30), "saurashtra": (69.80, 21.20), "jamnagar": (69.60, 22.80),
    "calcutta": (88.20, 21.50), "sharjah": (55.30, 25.40), "jask": (57.70, 25.60), "beirut": (35.40, 33.90), "nicosia": (33.70, 34.70), "cyprus": (33.70, 34.70),
    "izmir": (26.50, 38.50), "smyrna": (26.50, 38.50),
    # Europe
    "dover": (1.45, 51.05), "calais": (1.75, 51.05), "dungeness": (0.98, 50.88), "le touquet": (1.45, 50.53),
    "eastchurch": (0.95, 51.45), "land's end": (-5.90, 50.05), "lands end": (-5.90, 50.05), "eype mouth": (-2.80, 50.68), "portsmouth harbour": (-1.10, 50.78),
    "portsmouth": (-1.10, 50.75), "falmouth": (-5.00, 50.10), "alderney": (-2.20, 49.75), "brehec": (-3.00, 48.80), "benodet": (-4.10, 47.80),
    "channel coast, france": (-3.00, 48.85), "harwich": (1.60, 51.95), "thames estuary": (1.10, 51.50), "bridlington": (0.00, 54.10), "blackhall rocks": (-1.20, 54.75),
    "hebrides": (-7.80, 57.50), "isle of mull": (-6.30, 56.40), "anglesey": (-4.60, 53.40), "holyhead": (-4.80, 53.40), "dublin": (-5.80, 53.35),
    "cork": (-9.00, 51.50), "shannon, ireland": (-10.00, 52.50), "mayo": (-10.20, 54.00), "point lynas": (-4.30, 53.45),
    "rockall": (-14.00, 57.60), "bergen": (5.10, 60.40), "odda": (5.60, 60.00), "bodo": (14.20, 67.30), "kiel": (10.30, 54.50), "holmo": (20.90, 63.70),
    "roslagen": (19.00, 59.70), "raseborg": (23.40, 59.90), "scheldt": (3.60, 51.45), "cape finisterre": (-9.60, 42.90), "portugal": (-9.80, 39.50),
    "portuguese coast": (-9.80, 39.50), "lisbon": (-9.60, 38.60), "madeira": (-16.90, 32.60), "funchal": (-16.90, 32.60), "azores": (-27.50, 38.50),
    "terceira": (-27.20, 38.70), "pico island": (-28.30, 38.40), "santa maria": (-25.10, 36.95), "canary islands": (-15.50, 28.50), "canaries": (-15.50, 28.50),
    "safi": (-9.40, 32.50), "el jadida": (-8.60, 33.30), "gibraltar": (-5.35, 36.10), "formentera": (1.45, 38.60), "port d'andratx": (2.35, 39.50),
    "cap d'antibes": (7.13, 43.50), "corsica": (8.80, 42.50), "teluada": (8.60, 38.90), "sardinia": (8.60, 38.90), "sicily": (14.00, 37.20),
    "corfu": (19.90, 39.60), "st george's bay": (19.90, 39.40), "euboea": (24.30, 38.40), "cape matapan": (22.50, 36.30), "antikythera": (23.30, 35.90),
    "cattaro": (18.50, 42.30), "dardanelles": (26.20, 40.10), "marseille": (5.30, 43.20), "barcelona": (2.40, 41.30), "palermo": (13.40, 38.20),
    "naples": (14.20, 40.80), "leith": (-3.00, 56.05), "hamburg": (8.40, 54.00), "antwerp": (3.40, 51.50), "liverpool": (-3.40, 53.50),
    "london": (1.50, 51.45), "glasgow": (-5.00, 55.60), "hull": (0.20, 53.60), "avonmouth": (-2.90, 51.40), "belfast": (-5.70, 54.70),
    "england": (-5.00, 50.00), "bremerhaven": (8.30, 53.80), "plattsburgh": (-73.40, 44.70), "le havre": (0.00, 49.50),
    # Africa
    "dakar": (-17.60, 14.70), "senegal": (-17.60, 14.70), "bathurst": (-16.60, 13.50), "sierra leone": (-13.40, 8.40), "liberia": (-11.00, 6.20),
    "ivory coast": (-4.50, 5.00), "sao tome": (6.70, 0.40), "port etienne": (-17.10, 20.90), "cape verde": (-23.50, 15.50), "tristan da cunha": (-12.30, -37.10),
    "saint helena": (-5.70, -15.95), "cape town": (18.30, -33.90), "durban": (31.10, -29.90), "mbhashe river": (29.00, -32.30), "cape of good hope": (18.50, -34.40),
    "madagascar": (47.00, -26.00), "rodrigues": (63.40, -19.70),
    # Australia and New Zealand
    "sydney": (151.35, -33.85), "port jackson": (151.35, -33.85), "botany bay": (151.30, -34.00), "newcastle, australia": (151.85, -32.95), "newcastle": (151.85, -32.95),
    "wollongong": (151.00, -34.45), "hawkesbury": (151.35, -33.58), "lord howe island": (159.08, -31.55), "bermagui": (150.15, -36.43), "twofold bay": (149.95, -37.08),
    "gabo island": (149.95, -37.60), "melbourne": (144.70, -38.30), "port phillip": (144.70, -38.30), "port phillip bay": (144.70, -38.30), "port philip": (144.70, -38.30),
    "hobson's bay": (144.90, -37.87), "geelong": (144.60, -38.20), "cape otway": (143.50, -38.90), "king island": (143.90, -39.85), "hobart": (147.40, -43.05),
    "adventure bay": (147.40, -43.35), "blackman's bay": (147.32, -43.00), "cape pillar": (148.02, -43.25), "fortescue bay": (148.00, -43.13),
    "port arthur": (147.85, -43.15), "launceston": (146.80, -41.05), "table cape": (145.73, -40.95), "circular head": (145.30, -40.75), "swan island": (148.12, -40.73),
    "furneaux group": (148.00, -40.00), "kent group": (147.30, -39.45), "fremantle": (115.60, -32.05), "houtman abrolhos": (113.80, -28.70),
    "darwin": (130.75, -12.35), "truscott": (125.80, -14.10), "buckingham bay": (135.80, -12.10), "thursday island": (142.20, -10.55), "booby island": (141.90, -10.60),
    "cairns": (145.85, -16.85), "shute harbour": (148.85, -20.25), "gladstone": (151.40, -23.80), "cheviot beach": (144.65, -38.32), "williamtown": (152.20, -32.80),
    "wellington": (174.70, -41.35), "cook strait": (174.50, -41.30), "nelson": (173.30, -41.10), "lyttelton": (172.85, -43.60), "canterbury bight": (172.00, -44.30),
    "wairarapa": (176.20, -41.40), "russell, new zealand": (174.20, -35.20), "tauranga": (176.30, -37.60), "milford sound": (167.80, -44.60),
    "te henga": (174.43, -36.90), "bethells beach": (174.43, -36.90), "auckland island": (165.90, -50.70), "antipodes islands": (178.80, -49.70),
    "macquarie island": (158.90, -54.60), "southern new zealand": (167.50, -47.00), "new caledonia": (166.00, -22.50), "nakety bay": (166.10, -21.50),
    "vanuatu": (167.50, -16.50), "bellona": (159.80, -11.30), "rabaul": (152.30, -4.20), "blackett strait": (157.00, -8.10), "torokina": (155.05, -6.25),
    "guadalcanal": (159.90, -9.30), "open bay islands": (168.80, -43.85),
    # Great Lakes
    "benton harbor": (-86.65, 42.12), "south haven": (-86.40, 42.40), "holland, michigan": (-86.35, 42.80), "holland": (-86.35, 42.80), "ludington": (-86.60, 43.95),
    "manitowoc": (-87.50, 44.10), "muskegon": (-86.45, 43.23), "chicago": (-87.40, 41.90), "port washington": (-87.75, 43.40), "milwaukee": (-87.75, 43.05),
    "racine": (-87.65, 42.73), "green bay": (-87.70, 45.10), "manitou passage": (-85.95, 45.05), "gull island": (-86.65, 45.70), "poverty island": (-86.65, 45.53),
    "traverse city": (-85.75, 45.20), "huron islands": (-87.97, 46.95), "caribou island": (-85.80, 47.40), "two harbors": (-91.55, 46.95),
    "port arthur, ontario": (-89.05, 48.35), "niagara river": (-79.05, 43.25),
}

# Named seas and bays with a representative point. These give "Sea area only" confidence.
SEAS = {
    "bermuda triangle": (-70.4, 25.5), "caribbean sea": (-75.0, 15.0), "caribbean": (-75.0, 15.0), "west indies": (-66.0, 16.5), "gulf of mexico": (-90.0, 25.5),
    "straits of florida": (-81.0, 24.2), "florida strait": (-81.0, 24.2), "gulf of honduras": (-88.2, 16.2), "gulf of maine": (-68.5, 43.0),
    "labrador sea": (-55.0, 58.0), "beaufort sea": (-145.0, 71.5), "gulf of alaska": (-145.0, 57.5), "bering sea": (-178.0, 57.0),
    "north sea": (3.0, 56.0), "heligoland bight": (7.6, 54.2), "skagerrak": (9.5, 57.8), "skagerrak strait": (9.5, 57.8), "norwegian sea": (3.0, 66.0),
    "barents sea": (35.0, 74.0), "kara sea": (70.0, 74.0), "laptev sea": (125.0, 76.0), "east siberian sea": (160.0, 74.0), "baltic sea": (19.0, 57.0),
    "gulf of finland": (26.0, 59.8), "bay of biscay": (-5.0, 45.5), "celtic sea": (-7.5, 50.5), "mediterranean sea": (18.0, 35.5), "mediterranean": (18.0, 35.5),
    "tyrrhenian sea": (12.0, 40.0), "ionian sea": (18.5, 38.0), "adriatic sea": (15.5, 43.0), "aegean sea": (25.0, 38.5), "sea of azov": (36.5, 46.0),
    "persian gulf": (52.0, 27.0), "gulf of oman": (58.5, 24.5), "arabian sea": (65.0, 15.0), "bay of bengal": (88.0, 15.0), "red sea": (38.0, 20.0),
    "strait of malacca": (99.5, 4.0), "south china sea": (113.0, 14.0), "east china sea": (126.0, 29.5), "philippine sea": (132.0, 20.0),
    "java sea": (111.0, -5.0), "savu sea": (122.0, -9.5), "timor sea": (127.0, -11.0), "arafura sea": (135.0, -9.5), "coral sea": (153.0, -16.0),
    "tasman sea": (160.0, -37.0), "northwest passage": (-100.0, 70.0), "victoria strait": (-100.5, 69.3), "great barrier reef": (149.0, -19.5),
    "lake michigan": (-87.0, 43.8), "lake superior": (-87.5, 47.6), "lake huron": (-82.5, 44.8), "lake erie": (-81.2, 42.2), "river plate": (-56.8, -35.2),
    "gulf of st. lawrence": (-62.0, 48.0), "andaman sea": (96.5, 11.0), "gulf of california": (-110.5, 26.5), "bass strait": (146.5, -39.5), "irish sea": (-5.2, 53.6), "english channel": (-1.5, 50.2),
}

# whole oceans or worse: not enough to place an incident
OCEANS = ["north atlantic ocean", "south atlantic ocean", "atlantic ocean", "north atlantic", "south atlantic", "n atlantic", "atlantic",
          "pacific ocean", "north pacific ocean", "south pacific ocean", "central pacific ocean", "central pacific", "pacific theatre", "pacific",
          "indian ocean", "arctic ocean", "arctic sea", "antarctic ocean", "southern ocean", "high seas", "unknown", "location unknown"]

# land-only locations: when these are the only match, the incident is not at sea
LAND = ["argentina", "angola", "brazil", "bolivia", "burma", "china", "india", "peru", "russia", "soviet union", "ukraine", "estonia", "laos",
        "chile", "turkey", "mexico", "costa rica", "guyana", "pakistan", "malaysia", "papua new guinea", "new zealand", "australia", "canada",
        "united states", "alaska", "california", "michigan", "florida", "queensland", "new south wales", "antarctica", "sweden", "azerbaijan",
        "mauritania", "bangladesh", "france", "yukon", "venezuela", "colombia", "indonesia", "japan", "italy", "greece"]
