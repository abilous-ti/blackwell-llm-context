r"""Check that the MDPI-template variant says the same thing as the master.

The variant is generated, so the risk is not that someone edited it -- it is that the generator
dropped or mangled something silently. Two checks:

  1. Source level: every substantive line of the master's body and appendices must appear in the
     variant, modulo the transformations the generator is allowed to make (theorem environments
     capitalised, the manual appendix float renumbering removed).
  2. Rendered level: every number that appears in the master PDF must appear in the variant PDF.
     This is the one that would catch a table or a figure quietly failing to typeset.

Usage:  python paper/check_mdpi_drift.py
"""
import os, re, subprocess, sys, io, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "blackwell-paper.tex")
VAR = os.path.join(HERE, "_mdpi", "blackwell-paper-mdpi.tex")
MPDF = os.path.join(HERE, "blackwell-paper.pdf")
VPDF = os.path.join(HERE, "_mdpi", "blackwell-paper-mdpi.pdf")
os.environ["PATH"] = (os.environ.get("PATH", "") + os.pathsep +
                      r"C:\Users\AndriyBilous\AppData\Local\Programs\MiKTeX\miktex\bin\x64")

for p in (VAR, VPDF):
    if not os.path.exists(p):
        print("NOT CHECKED - %s missing; run paper/build_mdpi_variant.py first" % p)
        sys.exit(1)

ENVS = ["theorem", "proposition", "corollary", "lemma", "definition", "assumption", "remark"]
DROPPED = (r"\renewcommand{\thetable}{A\arabic{table}}",
           r"\renewcommand{\thefigure}{A\arabic{figure}}",
           r"\setcounter{table}{0}", r"\setcounter{figure}{0}",
           r"\bibliographystyle{plainnat}", r"\clearpage", r"\appendix")


def norm(t):
    for e in ENVS:
        t = t.replace(r"\begin{%s}" % e, r"\begin{%s}" % e.capitalize())
        t = t.replace(r"\end{%s}" % e, r"\end{%s}" % e.capitalize())
    return " ".join(t.split())


master = open(MASTER, encoding="utf-8").read().replace("\r\n", "\n")
var = norm(open(VAR, encoding="utf-8").read().replace("\r\n", "\n"))

body = master[master.index(r"\section{Introduction}"):master.index(r"\section*{Author Contributions}")]
app = master[master.index("\n\\appendix"):master.index(r"\end{document}")]

missing = []
for chunk, label in ((body, "body"), (app, "appendix")):
    for line in chunk.split("\n"):
        s = line.strip()
        if (not s or s.startswith("%") or len(s) < 25 or s in DROPPED):
            continue
        if norm(s) not in var:
            missing.append((label, s[:100]))

print("source check: %d substantive lines missing from the variant" % len(missing))
for lab, s in missing[:10]:
    print("   [%s] %s" % (lab, s))

# ---- rendered check ------------------------------------------------------------------------
def numbers(pdf):
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out = f.name
    subprocess.run(["pdftotext", pdf, out], capture_output=True)
    t = open(out, encoding="utf-8", errors="replace").read()
    os.unlink(out)
    # drop MDPI's submission line numbers and page furniture before harvesting
    t = re.sub(r"^\s*\d{1,4}\s*$", " ", t, flags=re.M)
    return t, set(re.findall(r"\d+/\d+|\d+\.\d{2,}|\d+(?:\.\d+)?%", t))


mt, mn = numbers(MPDF)
vt, vn = numbers(VPDF)
lost = sorted(mn - vn)
print("rendered check: master carries %d distinct numeric tokens, %d absent from the variant"
      % (len(mn), len(lost)))
for x in lost[:15]:
    print("   missing: %s" % x)

sys.exit(1 if (missing or lost) else 0)
