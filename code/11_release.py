"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23856868, https://doi.org/10.5281/zenodo.23856868 and https://blog.tristanhotham.com/2026/10/31/lost-at-sea/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Lost_at_Sea"
B = R["bermuda"]

# numbers written in words in the blog alt text and captions
d40 = [d for d in R["cat"]["decades"] if d["dec"] == 1940][0]
assert 100 <= sum(v for k, v in d40.items() if k != "dec") <= 115 and max(sum(v for k, v in d.items() if k != "dec") for d in R["cat"]["decades"]) == sum(v for k, v in d40.items() if k != "dec")
assert round(B["x"], 1) == 2.9 and round(B["lanes_x"], 1) == 2.4 and round(B["x46"]) == 6 and round(B["L_x"], 1) == 6.5 and round(B["neigh_x"], 1) == 2.7
assert R["areas"][[a["name"] for a in R["areas"]].index("Bermuda Triangle")]["T_ships"]["flag"] == "as expected"
assert B["M_flag"] == "as expected" and B["famous_inside_names"] == ["USS Cyclops", "BSAA Star Ariel"]
assert 1e-3 < B["p_up"] < .025                       # "just inside the upper 99.8% line"
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Lost at sea: is the Bermuda Triangle worse than its traffic?",
        "slug": "lost-at-sea",
        "excerpt": f"I placed {R['cat']['placed']} famous disappearances on the map and tested every sea against its shipping. The Bermuda Triangle has {B['o']} against {B['e']:.1f} expected, but its neighbours run just as high, and most of its famous cases happened outside it.",
        "seo_description": f"{R['cat']['placed']} famous disappearances at sea tested against shipping traffic: the Bermuda Triangle is no worse than its neighbours.",
        "tags": ["Bermuda Triangle", "maps", "data visualisation", "maritime history", "shipping", "AIS", "Wikipedia", "statistics", "open data"],
        "header_alt": f"Title card reading 'Lost at sea' in black and red on pale paper, asking whether the Bermuda Triangle is worse than its traffic would predict, with '{B['o']} v {B['e']:.1f}' in red, beside a map of the dashed Bermuda Triangle over blue shipping lanes with white and red dots for famous disappearances."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/lost-at-sea_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"lost-at-sea/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"lost-at-sea/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "lost-at-sea/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ")
zmeta = {"title": "Lost at Sea: Famous Disappearances Tested against Shipping Traffic",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/lost-at-sea/}}.</p><p>Data: Wikipedia contributors, lists of missing ships, missing aircraft and people who disappeared mysteriously at sea, the Bermuda Triangle, Devil's Sea and Lake Michigan Triangle articles, and lists of shipwrecks (CC BY-SA 4.0; derived tables shared under the same licence); Wikidata (CC0); World Bank, Global Shipping Traffic Density (IMF and World Bank, AIS data 2015 to 2021, CC BY 4.0); Natural Earth.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Bermuda Triangle", "disappearances at sea", "shipping traffic", "AIS", "funnel plot", "maritime history", "Wikipedia", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://en.wikipedia.org/wiki/List_of_missing_ships", "relation": "isDerivedFrom", "resource_type": "other"},
                                 {"identifier": "https://en.wikipedia.org/wiki/List_of_missing_aircraft", "relation": "isDerivedFrom", "resource_type": "other"},
                                 {"identifier": "https://en.wikipedia.org/wiki/List_of_people_who_disappeared_mysteriously_at_sea", "relation": "isDerivedFrom", "resource_type": "other"},
                                 {"identifier": "https://datacatalog.worldbank.org/search/dataset/0037580", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
