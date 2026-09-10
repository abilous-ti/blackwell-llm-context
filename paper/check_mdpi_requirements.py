r"""Check the MDPI-template variant against MAKE's Instructions for Authors.

Every rule below is quoted from https://www.mdpi.com/journal/make/instructions or from the
template's own guidance. Mechanical checks only -- things a script can decide. Items needing human
judgement are listed at the end as REVIEW, not silently passed.

Usage:  python paper/check_mdpi_requirements.py
"""
import os, re, subprocess, sys, io, zipfile, struct

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
VAR = os.path.join(HERE, "_mdpi", "blackwell-paper-mdpi.tex")
VPDF = os.path.join(HERE, "_mdpi", "blackwell-paper-mdpi.pdf")
FIGZIP = os.path.join(HERE, "submission", "blackwell-paper-figures.zip")
os.environ["PATH"] = (os.environ.get("PATH", "") + os.pathsep +
                      r"C:\Users\AndriyBilous\AppData\Local\Programs\MiKTeX\miktex\bin\x64")
if not os.path.exists(VAR):
    print("run paper/build_mdpi_variant.py first"); sys.exit(1)
s = open(VAR, encoding="utf-8").read()

ok, bad, review = [], [], []


def check(cond, label, detail=""):
    (ok if cond else bad).append((label, detail))


# ---- front matter -------------------------------------------------------------------------
abst = re.search(r"\\abstract\{(.*?)\}\n\\keyword", s, re.S)
words = len(re.sub(r"\\[a-zA-Z]+|[{}$\\%]", " ", abst.group(1)).split()) if abst else 0
check(abst is not None, "abstract present")
check(words <= 200, "abstract <= ~200 words", "%d words" % words)
check(abst and "\n\n" not in abst.group(1).strip(), "abstract is a single paragraph")
kw = re.search(r"\\keyword\{(.*?)\}", s, re.S)
n_kw = len([k for k in kw.group(1).split(";") if k.strip()]) if kw else 0
check(3 <= n_kw <= 10, "keywords between 3 and 10", "%d" % n_kw)
check(bool(re.search(r"\\Title\{[^}]{10,}\}", s)), "title present")
check("\\AuthorNames{" in s, "AuthorNames (PDF metadata) present")
check(bool(re.search(r"\\corres\{Correspondence:", s)), "corresponding author designated")
# PubMed/MEDLINE affiliation format: street, zip, city, country
addr = re.search(r"\\address\{(.*?)\n\\corres", s, re.S)
a = addr.group(1) if addr else ""
check("Ukraine" in a and re.search(r"\b\d{5}\b", a), "affiliations carry zip code and country")
check(a.count("@") >= 1, "author e-mails in the affiliation block")
check(len(re.findall(r"orcidauthor[A-Z]", s)) >= 4, "ORCID iDs supplied for all authors")

# ---- required sections --------------------------------------------------------------------
for sec in ("Introduction", "Materials and Methods", "Results", "Discussion", "Conclusion"):
    check(bool(re.search(r"\\(sub)?section\{%s" % sec, s)), "section present: %s" % sec)
for macro in ("authorcontributions", "funding", "institutionalreview", "informedconsent",
              "dataavailability", "acknowledgments", "conflictsofinterest", "abbreviations"):
    check(("\\%s{" % macro) in s, "back matter: \\%s" % macro)

# ---- prescribed wording --------------------------------------------------------------------
check("The authors have reviewed and edited the output and take full responsibility" in s,
      "GenAI: MDPI's prescribed Acknowledgments sentence")
check("Use of generative AI in this study" in s or "generative AI" in s.split("Results")[0],
      "GenAI: disclosed in Materials and Methods")
conf = re.search(r"\\conflictsofinterest\{(.*?)\}", s, re.S)
cw = conf.group(1).strip() if conf else ""
check(cw.startswith("The authors declare no conflict"), "conflicts statement uses MDPI wording", cw[:60])
check("no external funding" in s or "funded by" in s, "funding statement is explicit")

# ---- floats -------------------------------------------------------------------------------
n_tab = len(re.findall(r"\\begin\{table", s))
n_fig = len(re.findall(r"\\begin\{figure", s))
caps = len(re.findall(r"\\caption\{", s))
check(caps >= n_tab + n_fig, "every float has a caption", "%d floats, %d captions" % (n_tab + n_fig, caps))
# The 8pt floor is a TABLE rule: "To facilitate the copy-editing of larger tables, smaller fonts
# (no smaller than 8 pt.) may be used." Figure labels are governed by legibility, not by this, so
# the check looks inside table environments only -- an earlier version flagged TikZ tick labels.
tables = re.findall(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", s, re.S)
small_tab = [t for t in tables if re.search(r"\\(tiny|scriptsize)\b", t)]
check(not small_tab, "no table font below 8pt (\\tiny/\\scriptsize inside a table)",
      "%d table(s) affected" % len(small_tab))
tiny_fig = len(re.findall(r"\\tiny\b", s)) - sum(len(re.findall(r"\\tiny\b", t)) for t in tables)
if tiny_fig:
    review.append("Figure labels use \\tiny %d times. MDPI's 8pt floor covers tables, not figures, "
                  "but at the class's 9pt base \\tiny is about 5pt -- check the figures read "
                  "cleanly in the MDPI layout." % tiny_fig)

# ---- references ----------------------------------------------------------------------------
check(s.count(r"\bibliography{") == 1, "exactly one \\bibliography call",
      "%d found" % s.count(r"\bibliography{"))
check("Definitions/mdpi" in s, "MDPI bibliography style")
if os.path.exists(VPDF):
    txt = os.path.join(HERE, "_mdpi", "_req.txt")
    subprocess.run(["pdftotext", "-layout", VPDF, txt], capture_output=True)
    t = open(txt, encoding="utf-8", errors="replace").read()
    os.unlink(txt)
    refs = [int(x) for x in re.findall(r"^ *(\d{1,3})\. [A-Z]", t, re.M)]
    cites = [int(x) for x in re.findall(r"\[(\d{1,3})\]", t)]
    hi_ref, hi_cite = (max(refs) if refs else 0), (max(cites) if cites else 0)
    check(hi_cite <= hi_ref and hi_ref > 0,
          "every citation number is within the reference list",
          "highest reference %d, highest citation %d" % (hi_ref, hi_cite))
    check("??" not in t and "TODO" not in t and "PLACEHOLDER" not in t.upper(),
          "no unresolved refs or placeholders in the PDF")

# ---- figures ZIP ----------------------------------------------------------------------------
if os.path.exists(FIGZIP):
    with zipfile.ZipFile(FIGZIP) as z:
        names = z.namelist()
        dpis = []
        for n in names:
            d = z.read(n)
            i = d.find(b"pHYs")
            dpis.append(round(struct.unpack(">I", d[i + 4:i + 8])[0] * 0.0254) if i > 0 else 0)
    check(all(n.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")) for n in names),
          "figures are PNG/JPEG/TIFF", ", ".join(names))
    check(all(x >= 600 for x in dpis), "figures at >= 600 dpi", str(dpis))
else:
    bad.append(("figures ZIP present", FIGZIP))

review.extend([
    "Cover letter: MAKE's two required statements must be confirmed true by an author.",
    "Reviewer suggestions: entered in the submission system, not the cover letter.",
    "Acronyms must be defined at first use in the abstract, the main text, and the first "
    "figure/table -- a script cannot judge this reliably.",
    "Float placement: MDPI's narrower text block reflows tables; check wide tables visually.",
    "Graphical abstract is optional and not supplied.",
])

print("PASS %d / FAIL %d" % (len(ok), len(bad)))
print()
for l, d in ok:
    print("  ok    %s%s" % (l, ("  (%s)" % d) if d else ""))
if bad:
    print()
    for l, d in bad:
        print("  FAIL  %s%s" % (l, ("  (%s)" % d) if d else ""))
print()
print("Needs a human:")
for r in review:
    print("  - %s" % r)
sys.exit(1 if bad else 0)
