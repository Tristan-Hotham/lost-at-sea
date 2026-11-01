"""Parse the three Wikipedia lists (missing ships, missing aircraft, people who disappeared mysteriously at sea) into one
row per incident, keeping the location text. Tables are read with their row spans filled in. In the people list, rows
that continue a row span (the second Vivaldi brother, the Briggs family) are folded into one incident. The "Solved cases"
tables of the people list are left out."""
import re
from bs4 import BeautifulSoup
from common import *


def clean(cell):
    for s in cell.select("sup.reference, .mw-ref, style, .sortkey, span[style*='display:none']"):
        s.decompose()
    t = re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()
    t = re.sub(r"\s+([,.;:)])", r"\1", t).replace("( ", "(")
    return t


def grid(table):
    """Table rows as lists of cell texts, with rowspan and colspan filled in. Returns (rows, spanned) where spanned marks
    cells copied down from a row span."""
    rows, carry = [], {}
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        out, spanned, ci = [], [], 0
        it = iter(cells)
        pending = list(cells)
        while pending or ci in carry:
            if ci in carry:
                txt, left = carry[ci]
                out.append(txt); spanned.append(True)
                if left <= 1: del carry[ci]
                else: carry[ci] = (txt, left - 1)
                ci += 1
                continue
            c = pending.pop(0)
            txt = clean(c)
            rs = int(re.sub(r"\D", "", c.get("rowspan", "1")) or 1); cs = int(re.sub(r"\D", "", c.get("colspan", "1")) or 1)
            for _ in range(cs):
                out.append(txt); spanned.append(False)
                if rs > 1: carry[ci] = (txt, rs - 1)
                ci += 1
        rows.append((out, spanned))
    return rows


def year_of(s):
    m = re.findall(r"(?<!\d)(1[0-9]\d\d|20[0-2]\d)(?!\d)", s or "")
    return int(m[0]) if m else None


def sections(t):
    hs = t.find_all_previous(["h2", "h3"], limit=4)
    h2 = next((clean(h) for h in hs if h.name == "h2"), "")
    h3 = next((clean(h) for h in hs if h.name == "h3"), "")
    return h2, h3


def parse():
    out = []
    # ---- ships
    s = BeautifulSoup(jload(f"{RAW6}/lost/wiki_missing_ships.json")["html"], "lxml")
    for t in s.find_all("table", class_="wikitable"):
        h2, h3 = sections(t)
        rows = grid(t)
        hd = [x.lower() for x in rows[0][0]]
        for cs, sp in rows[1:]:
            if len(cs) < 3 or not cs[0]: continue
            out.append({"list": "ships", "kind": 0, "name": cs[0], "date": cs[1], "year": year_of(cs[1]), "where": cs[2],
                        "context": cs[2], "section": f"{h2} / {h3}".strip(" /")})
    # ---- aircraft
    s = BeautifulSoup(jload(f"{RAW6}/lost/wiki_missing_aircraft.json")["html"], "lxml")
    for t in s.find_all("table", class_="wikitable"):
        rows = grid(t)
        for cs, sp in rows[1:]:
            if len(cs) < 6 or not cs[1]: continue
            out.append({"list": "aircraft", "kind": 1, "name": cs[1], "date": cs[0], "year": year_of(cs[0]), "where": cs[4],
                        "context": cs[5], "people": cs[2], "section": ""})
    # ---- people
    s = BeautifulSoup(jload(f"{RAW6}/lost/wiki_people_disappeared_at_sea.json")["html"], "lxml")
    for t in s.find_all("table", class_="wikitable"):
        h2, h3 = sections(t)
        if "Solved" in h2 or "Solved" in h3 or any("Solved" in clean(h) for h in t.find_all_previous("h2", limit=1)):
            continue
        rows = grid(t)
        last = None
        for cs, sp in rows[1:]:
            if len(cs) < 5: continue
            date, person, where, circ = cs[0], cs[1], cs[3], cs[4]
            if last and sp[0] and date == last["date"] and where == last["where"] and circ == last["context"]:
                last["persons"].append(person); continue
            last = {"list": "people", "kind": 2, "name": person, "date": date, "year": year_of(date), "where": where,
                    "context": circ, "persons": [person], "section": ""}
            out.append(last)
    return out


if __name__ == "__main__":
    rows = parse()
    import collections
    print(collections.Counter(r["list"] for r in rows))
    jsave(rows, f"{WORK}/list_rows.json", indent=1)
