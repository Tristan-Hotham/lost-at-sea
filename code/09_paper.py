"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Lost_at_Sea"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
VERD = {"higher": "clearly more", "higher (95%)": "more (95\\%)", "as expected": "as expected", "lower (95%)": "fewer (95\\%)", "lower": "clearly fewer"}


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f in ("f1", "x1"): return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    return tex(str(v))


r2 = lambda x: "n/a" if x is None else f"{x:.2f}" if x < 10 else f"{x:.0f}"
rows = "".join(f"{tex(a['name'])} & {a['traffic_pct']:.2f} & {a['T']['o']} & {a['T']['e']:.2f} & {r2(a['T']['ratio'])} & {r2(a['T']['lo'])} to {r2(a['T']['hi'])} & {VERD[a['T']['flag']]} & {r2(a['L']['ratio']) if a['L'] else 'n/a'} & {a['M']['o']} / {a['M']['e']:.1f}\\\\\n"
               for a in sorted(R["areas"], key=lambda a: -(a["T"]["ratio"] or 0)))
TA = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Test T for every area, sorted by ratio, with test L (ratio against recorded losses of 1800 to 2025) and test M (recorded losses 2000 to 2025, observed / expected).}\\label{tab:areas}"
      "\\begin{tabular}{p{4.0cm}rrrrrlrr}\\toprule Area & Traffic \\% & O & E & O/E & 95\\% interval & Verdict & L: O/E & M: O / E\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
F = R["famous"]["Bermuda Triangle"]["list"]
rows = "".join(f"{tex(f['name'])} & {f['year']} & {tex(f['conf'].lower())} & {'inside' if f['inside'] else 'not placed' if f['km'] is None else str(f['km']) + ' km'}\\\\\n" for f in F)
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{Incidents told in the Wikipedia article on the Bermuda Triangle: how each was placed and how far outside the Miami, Bermuda and San Juan triangle it falls.}\\label{tab:famous}"
      "\\begin{tabular}{p{6.2cm}rp{3.4cm}r}\\toprule Incident & Year & Placed by & Outside by\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(w['name'])} & {w['o']} & {w['e']:.2f} & {r2(w['x'])} & {r2(w['lanes_x'])} & {tex(w['causes'])}\\\\\n" for w in R["worse"])
TW = ("\\begin{table}[tbp]\\centering\\small\\caption{Areas clearly worse than their traffic predicts (beyond the 99.8\\% funnel limit), with the ratio under the lanes index and the likely reasons.}\\label{tab:worse}"
      "\\begin{tabular}{p{4.6cm}rrrrp{3.6cm}}\\toprule Area & O & E & O/E & Lanes O/E & Likely reasons\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
sq = lambda c: f"{abs(c['lat0'] + (2 if c['lat0'] < 0 else 0)):.0f} to {abs(c['lat0'] + (0 if c['lat0'] < 0 else 2)):.0f}{'S' if c['lat0'] < 0 else 'N'}, {abs(c['lon0'] + (2 if c['lon0'] < 0 else 0)):.0f} to {abs(c['lon0'] + (0 if c['lon0'] < 0 else 2)):.0f}{'W' if c['lon0'] < 0 else 'E'}"
rows = "".join(f"{tex(c['place'])} & {sq(c)} & {c['D']} & {'under 0.001' if c['D_exp'] < .001 else f'{c[chr(68) + chr(95) + chr(101) + chr(120) + chr(112)]:.3f}'} & {tex(c['causes'])}\\\\\n" for c in R["cells"]["ranked"][:16])
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{The 2 degree squares furthest beyond their traffic (at least two incidents and beyond the 99.8\\% limit; the 16 most extreme of " + str(R["cells"]["n_flagged"]) + ").}\\label{tab:cells}"
      "\\begin{tabular}{p{4.6cm}p{3.2cm}rrp{3.2cm}}\\toprule Square & Extent & O & E & Likely reasons\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("{{meta.doi}}", "@@DOI@@")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("AREAS", TA), ("FAMOUS", TF), ("WORSE", TW), ("CELLS", TC)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("\\href{https://doi.org/@@DOI@@}{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "@@" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
