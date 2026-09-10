r"""Assemble the MAKE submission bundle.

MAKE takes LaTeX as "one ZIP folder (including all source files and images, so that the Editorial
Office can recompile the submitted PDF)", and figures separately "in a single zip archive ... at a
sufficiently high resolution (preferably no less than 600 dpi) in PNG, JPEG or TIFF formats".

This writes paper/submission/ containing both ZIPs, the PDF, and the cover-letter draft, and
verifies the LaTeX ZIP by recompiling it in a scratch directory from its own contents alone -- if
the editorial office cannot rebuild the PDF from what we send, the submission stalls.

Usage:  python paper/make_submission_bundle.py
"""
import os, shutil, subprocess, sys, io, zipfile, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
# The built variant lives inside this repository; it used to be taken from another checkout,
# so the ZIP could carry a document nobody could rebuild from what is published here.
OUTDIR = os.environ.get("BLACKWELL_BUILD_DIR", os.path.join(HERE, "_build"))
SUB = os.path.join(HERE, "submission")
MIKTEX = os.environ.get("MIKTEX_BIN", os.path.expanduser(
    r"~\AppData\Local\Programs\MiKTeX\miktex\bin\x64"))
os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + MIKTEX

os.makedirs(SUB, exist_ok=True)

# --- 1. the LaTeX source ZIP -------------------------------------------------------------
# The .bbl is included deliberately: it lets the office recompile without running bibtex.
SRC = [(os.path.join(OUTDIR, "blackwell-paper-make.tex"), "blackwell-paper-make.tex"),
       (os.path.join(OUTDIR, "blackwell-paper-make.bbl"), "blackwell-paper-make.bbl"),
       (os.path.join(HERE, "blackwell-paper.bib"), "blackwell-paper.bib")]
missing = [p for p, _ in SRC if not os.path.exists(p)]
if missing:
    print("NOT BUILT - missing source files:")
    for m in missing:
        print("   " + m)
    sys.exit(1)

zip_src = os.path.join(SUB, "blackwell-paper-make-latex.zip")
with zipfile.ZipFile(zip_src, "w", zipfile.ZIP_DEFLATED) as z:
    for path, name in SRC:
        z.write(path, name)
print("ok    LaTeX source ZIP  %s (%d files)" % (os.path.basename(zip_src), len(SRC)))

# --- 2. the figures ZIP ------------------------------------------------------------------
figdir = os.path.join(HERE, "figures")
pngs = sorted(f for f in os.listdir(figdir) if f.lower().endswith(".png")) \
    if os.path.isdir(figdir) else []
if not pngs:
    print("NOT BUILT - no figures in paper/figures/; run paper/export_figures.py first")
    sys.exit(1)
zip_fig = os.path.join(SUB, "blackwell-paper-figures.zip")
with zipfile.ZipFile(zip_fig, "w", zipfile.ZIP_DEFLATED) as z:
    for f in pngs:
        z.write(os.path.join(figdir, f), f)
print("ok    figures ZIP       %s (%s)" % (os.path.basename(zip_fig), ", ".join(pngs)))

# --- 3. the PDF -------------------------------------------------------------------------
pdf_src = os.path.join(OUTDIR, "blackwell-paper-make.pdf")
if os.path.exists(pdf_src):
    shutil.copy2(pdf_src, os.path.join(SUB, "blackwell-paper-make.pdf"))
    print("ok    PDF               blackwell-paper-make.pdf (%.1f MB)"
          % (os.path.getsize(pdf_src) / 1e6))

# --- 4. verify the ZIP actually recompiles, alone ---------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    with zipfile.ZipFile(zip_src) as z:
        z.extractall(tmp)
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                        "blackwell-paper-make.tex"],
                       capture_output=True, text=True, cwd=tmp)
    built = os.path.join(tmp, "blackwell-paper-make.pdf")
    if r.returncode != 0 or not os.path.exists(built):
        print("\nFAIL  the LaTeX ZIP does not recompile on its own:")
        tail = [l for l in (r.stdout or "").split("\n") if l.startswith("!")][:5]
        for l in tail:
            print("   " + l)
        sys.exit(1)
    # a second pass so cross-references and the bibliography settle
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "blackwell-paper-make.tex"],
                   capture_output=True, text=True, cwd=tmp)
    log = open(os.path.join(tmp, "blackwell-paper-make.log"), encoding="utf-8",
               errors="replace").read()
    pages = ""
    for line in log.split("\n"):
        if "Output written" in line:
            pages = line.strip()
    undef = log.count("Citation") and "undefined" in log
    print("ok    ZIP recompiles standalone: %s" % pages)
    if "undefined" in log.lower():
        bad = [l for l in log.split("\n") if "undefined" in l.lower()][:3]
        print("      note - undefined references in the standalone build:")
        for b in bad:
            print("        " + b.strip()[:110])

print("\nbundle in %s" % SUB)
for f in sorted(os.listdir(SUB)):
    print("   %-38s %8.1f KB" % (f, os.path.getsize(os.path.join(SUB, f)) / 1024))
