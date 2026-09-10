r"""Export the three TikZ figures as standalone 600 dpi PNGs for MDPI submission.

MAKE asks for figures in a separate ZIP, "at a sufficiently high resolution (preferably no less
than 600 dpi) in PNG, JPEG or TIFF formats". The figures in this paper are TikZ, drawn inline, so
there are no image files to collect: each one is extracted here into a standalone document,
compiled, and rasterized at 600 dpi. Nothing in the manuscript changes.

Usage:  python paper/export_figures.py        (writes paper/figures/Figure_{1,2,3}.png)
"""
import os, re, subprocess, sys, shutil, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "blackwell-paper.tex")
OUT = os.path.join(HERE, "figures")
WORK = os.path.join(HERE, "_figwork")
MIKTEX = r"C:\Users\AndriyBilous\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + MIKTEX

src = open(TEX, encoding="utf-8").read().replace("\r\n", "\n")

# The figures are the tikzpicture bodies inside the three figure environments, in order.
figs = []
for m in re.finditer(r"\\begin\{figure\}.*?\\end\{figure\}", src, re.S):
    block = m.group(0)
    label = re.search(r"\\label\{(fig:[^}]+)\}", block)
    pics = re.findall(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", block, re.S)
    if pics:
        figs.append((label.group(1) if label else "fig%d" % (len(figs) + 1), "\n".join(pics)))

if not figs:
    print("no tikz figures found")
    sys.exit(1)

# Anything the figure bodies rely on from the manuscript preamble. Keep this minimal and explicit
# rather than splicing the whole preamble, which pulls in geometry/natbib/hyperref that a
# standalone document does not want.
PREAMBLE = "\n".join([
    r"\documentclass[border=6pt]{standalone}",
    r"\usepackage[T1]{fontenc}",
    r"\usepackage{lmodern}",
    r"\usepackage{amsmath,amssymb}",
    r"\usepackage{tikz}",
    r"\newcommand{\Dcal}{\mathcal{D}}",
    r"\newcommand{\PASS}{\mathrm{PASS}}",
    r"\newcommand{\dhat}{\hat{\delta}}",
    r"\newcommand{\Bord}{\succeq_{B}}",
])

os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)
made = []
for i, (label, body) in enumerate(figs, start=1):
    stem = "Figure_%d" % i
    tex = os.path.join(WORK, stem + ".tex")
    open(tex, "w", encoding="utf-8", newline="\n").write(
        PREAMBLE + "\n\\begin{document}\n" + body + "\n\\end{document}\n")
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                        "-output-directory", WORK, tex],
                       capture_output=True, text=True, cwd=WORK)
    pdf = os.path.join(WORK, stem + ".pdf")
    if r.returncode != 0 or not os.path.exists(pdf):
        print("FAIL  %s (%s): %s" % (stem, label,
                                     (r.stdout or "")[-400:].replace("\n", " ")[-300:]))
        continue
    subprocess.run(["pdftoppm", "-png", "-r", "600", "-singlefile", pdf,
                    os.path.join(OUT, stem)], check=True)
    png = os.path.join(OUT, stem + ".png")
    made.append((stem, label, os.path.getsize(png)))
    print("ok    %-10s %-14s %7.1f KB" % (stem, label, os.path.getsize(png) / 1024))

shutil.rmtree(WORK, ignore_errors=True)
print("\n%d of %d figures exported to paper/figures/ at 600 dpi" % (len(made), len(figs)))
if len(made) != len(figs):
    sys.exit(1)
