r"""Build the official-template variant: blackwell-paper-mdpi.tex on Definitions/mdpi.cls.

MAKE accepts free-format submission, so this is not required to submit. It is worth having anyway:
MDPI say using the template "will substantially shorten the time to complete copy-editing", and the
manuscript has to be reformatted into it at revision regardless.

The master is not touched. This reads it and emits a second file, so every guard that runs against
the master keeps running against the master.

LICENCE NOTE. The template ZIP carries MDPI's restriction: "Usage of these templates is exclusively
intended for submission to the journal for peer review, and strictly limited to this purpose and it
cannot be used for posting online on preprint servers or other websites." The class and style files
therefore live in paper/_mdpi/, which is gitignored, and must NOT be committed to the public
repository. They belong in the submission ZIP, which goes to MDPI, and nowhere else.

Set up once:
    download https://res.mdpi.com/data/MDPI_template_ACS.zip and unzip its Definitions/ folder
    into paper/_mdpi/Definitions/

Usage:  python paper/build_mdpi_variant.py
"""
import os, re, shutil, subprocess, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "blackwell-paper.tex")
WORK = os.path.join(HERE, "_mdpi")
DEFS = os.path.join(WORK, "Definitions")
OUT = os.path.join(WORK, "blackwell-paper-mdpi.tex")
MIKTEX = r"C:\Users\AndriyBilous\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + MIKTEX

if not os.path.isdir(DEFS):
    print("NOT BUILT - paper/_mdpi/Definitions/ is missing.")
    print("Download MDPI_template_ACS.zip and unzip its Definitions/ folder there.")
    sys.exit(1)

src = open(MASTER, "rb").read().decode("utf-8").replace("\r\n", "\n")
NL = "\n"

# ---- pull the pieces we need out of the master ------------------------------------------
abstract = re.search(r"\\begin\{abstract\}\n(.*?)\n\\end\{abstract\}", src, re.S).group(1)
abstract = " ".join(abstract.split())
kw = re.search(r"\\noindent\\textbf\{Keywords:\}(.*?)\n\n", src, re.S).group(1)
kw = " ".join(kw.split()).rstrip(".")

# body: from the first \section after \maketitle up to the back matter
body_start = src.index(r"\section{Introduction}")
body_end = src.index(r"\section*{Author Contributions}")
body = src[body_start:body_end]

# The appendices sit AFTER the back matter in the master, so they are lifted separately;
# mdpi.cls renumbers appendix floats itself via \appendixstart, so the master's manual
# \renewcommand{\thetable}{A...} block is dropped rather than fighting it.
app = src[src.index("\n\\appendix") + 1:src.index(r"\end{document}")]
app = app.replace(r"\appendix", "", 1)
for line in (r"\renewcommand{\thetable}{A\arabic{table}}",
             r"\renewcommand{\thefigure}{A\arabic{figure}}",
             r"\setcounter{table}{0}", r"\setcounter{figure}{0}",
             # The master calls \bibliography at the very end, i.e. INSIDE this slice. Leaving it
             # in printed the whole reference list twice -- 144 entries for 72 sources, with every
             # citation number in the second half wrong.
             r"\bibliography{blackwell-paper}"):
    app = app.replace(line, "")

# Abbreviations is a \section* in the master and a macro in the class.
_i = src.index(r"\section*{Abbreviations}")
_j = src.index("\n% =", _i)
abbrev = src[_i:_j].split("}", 1)[1].strip()

# the macro block, minus the \newtheorem lines (mdpi.cls supplies the environments)
macros = re.findall(r"^\\newcommand\{.*$", src[:body_start], re.M)
macros = [m for m in macros if "orcidlink" not in m]


def backmatter(name):
    """Text of a \\section*{name} block in the master."""
    i = src.index("\\section*{%s}" % name)
    j = src.index("\n\\section", i + 1)
    t = src[i:j].split("}", 1)[1]
    return " ".join(t.split())


# ---- theorem environments: ours are lowercase, mdpi.cls provides capitalised ones ---------
ENVS = ["theorem", "proposition", "corollary", "lemma", "definition", "assumption", "remark"]


def capitalise_envs(t):
    for e in ENVS:
        t = re.sub(r"\\begin\{%s\}" % e, r"\\begin{%s}" % e.capitalize(), t)
        t = re.sub(r"\\end\{%s\}" % e, r"\\end{%s}" % e.capitalize(), t)
    return t


# the appendices carry remarks and propositions too, so both halves need the mapping
body = capitalise_envs(body)
app = capitalise_envs(app)
# mdpi.cls has no \begin{proof}; amsthm's is available through the class
body = body.replace(r"\subsection*{Proof of", r"\subsection*{Proof of")

# appendices: the master opens them with \appendix
body = body.replace(r"\appendix", r"\appendixtitles{yes}" + NL + r"\appendix")

FRONT = NL.join([
    r"% ==========================================================================",
    r"%  Built from blackwell-paper.tex by paper/build_mdpi_variant.py -- do not edit by hand.",
    r"%  Requires Definitions/ from MDPI_template_ACS.zip alongside this file.",
    r"% ==========================================================================",
    r"\documentclass[make,article,submit,pdftex,moreauthors]{Definitions/mdpi}",
    r"",
    r"\usepackage{tikz}",
    r"",
    NL.join(macros),
    r"",
    # The class dereferences these at \begin{document}; leaving them out makes it fail there.
    r"\firstpage{1}",
    r"\makeatletter",
    r"\setcounter{page}{\@firstpage}",
    r"\makeatother",
    r"\pubvolume{1}",
    r"\issuenum{1}",
    r"\articlenumber{0}",
    r"\pubyear{2026}",
    r"\copyrightyear{2026}",
    r"\datereceived{ }",
    r"\dateaccepted{ }",
    r"\datepublished{ }",
    r"",
    r"\Title{Context Selection as a Partial Order: A Blackwell Framework and Verified LLM Evidence}",
    r"\newcommand{\orcidauthorA}{0009-0006-5467-7932}",
    r"\newcommand{\orcidauthorB}{0000-0002-9676-0180}",
    r"\newcommand{\orcidauthorC}{0000-0002-0359-5025}",
    r"\newcommand{\orcidauthorD}{0000-0002-5986-4618}",
    r"\Author{Andriy Bilous $^{1}$\orcidA{}, Vasyl Lytvyn $^{1}$\orcidB{}, "
    r"Petro Pukach $^{2,}$*\orcidC{} and Zoriana Rybchak $^{1}$\orcidD{}}",
    r"\AuthorNames{Andriy Bilous, Vasyl Lytvyn, Petro Pukach and Zoriana Rybchak}",
    r"\address{%",
    r"$^{1}$ \quad Department of Information Systems and Networks, Institute of Computer Science and "
    r"Information Technologies, Lviv Polytechnic National University, S. Bandery St. 12, "
    r"79013 Lviv, Ukraine; andriy.bilous@uitware.com (A.B.); vasyl.v.lytvyn@lpnu.ua (V.L.); "
    r"zoriana.l.rybchak@lpnu.ua (Z.R.)\\",
    r"$^{2}$ \quad Institute of Applied Mathematics and Fundamental Sciences, Lviv Polytechnic "
    r"National University, S. Bandery St. 12, 79013 Lviv, Ukraine}",
    r"\corres{Correspondence: petro.y.pukach@lpnu.ua}",
    r"",
    r"\abstract{%s}" % abstract,
    r"\keyword{%s}" % kw,
    r"",
    r"\begin{document}",
])

BACK = NL.join([
    r"\authorcontributions{%s}" % backmatter("Author Contributions"),
    r"\funding{%s}" % backmatter("Funding"),
    r"\institutionalreview{%s}" % backmatter("Institutional Review Board Statement"),
    r"\informedconsent{%s}" % backmatter("Informed Consent Statement"),
    r"\dataavailability{%s}" % backmatter("Data Availability Statement"),
    r"\acknowledgments{%s}" % backmatter("Acknowledgments"),
    r"\conflictsofinterest{%s}" % backmatter("Conflicts of Interest"),
    r"",
    r"\abbreviations{Abbreviations}{%",
    abbrev,
    r"}",
    r"",
    r"\appendixtitles{yes}",
    r"\appendixstart",
    r"\appendix",
    app,
    r"",
    r"\begin{adjustwidth}{-\extralength}{0cm}",
    r"\reftitle{References}",
    r"\bibliographystyle{Definitions/mdpi}",
    r"\bibliography{blackwell-paper}",
    r"\end{adjustwidth}",
    r"\end{document}",
])

open(OUT, "w", encoding="utf-8", newline="\n").write(FRONT + NL + NL + body + NL + BACK + NL)
print("ok    wrote %s" % os.path.relpath(OUT, HERE))

# the bib must sit beside it for bibtex
shutil.copy2(os.path.join(HERE, "blackwell-paper.bib"), WORK)

# ---- compile -----------------------------------------------------------------------------
stem = "blackwell-paper-mdpi"
for i, cmd in enumerate([["pdflatex", "-interaction=nonstopmode", stem],
                         ["bibtex", stem],
                         ["pdflatex", "-interaction=nonstopmode", stem],
                         ["pdflatex", "-interaction=nonstopmode", stem]]):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=WORK)
log = open(os.path.join(WORK, stem + ".log"), encoding="utf-8", errors="replace").read()
errs = [l for l in log.split("\n") if l.startswith("!")]
undef = sorted(set(re.findall(r"(?:Reference|Citation) `([^']+)' on page", log)))
pages = [l for l in log.split("\n") if "Output written" in l]

# ---- submission ZIP, kept inside the gitignored tree because it carries Definitions/ -------
if not errs and pages:
    import zipfile
    sub = os.path.join(WORK, "submission")
    os.makedirs(sub, exist_ok=True)
    z_path = os.path.join(sub, "blackwell-paper-mdpi-latex.zip")
    with zipfile.ZipFile(z_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in (stem + ".tex", stem + ".bbl", "blackwell-paper.bib"):
            z.write(os.path.join(WORK, f), f)
        for f in sorted(os.listdir(DEFS)):
            z.write(os.path.join(DEFS, f), "Definitions/" + f)
    shutil.copy2(os.path.join(WORK, stem + ".pdf"), os.path.join(sub, stem + ".pdf"))
    print("ok    submission ZIP  %s (%.1f MB, includes Definitions/)"
          % (os.path.relpath(z_path, HERE), os.path.getsize(z_path) / 1e6))
    print("      NOTE this ZIP contains MDPI's class files: send it to MDPI, do not commit it.")

print("      errors: %d   undefined refs/citations: %d" % (len(errs), len(undef)))
for e in errs[:6]:
    print("        " + e[:120])
for u in undef[:8]:
    print("        undefined: " + u)
if pages:
    print("      " + pages[0].strip())
if errs or not pages:
    sys.exit(1)

# A clean compile is not evidence the variant says the same thing: the duplicated bibliography
# compiled without a single error and printed 144 entries for 72 sources. Check content too.
d = subprocess.run([sys.executable, os.path.join(HERE, "check_mdpi_drift.py")],
                   capture_output=True, text=True)
print(d.stdout.rstrip())
r2 = subprocess.run([sys.executable, os.path.join(HERE, "check_mdpi_requirements.py")],
                   capture_output=True, text=True)
print(r2.stdout.rstrip())
sys.exit(d.returncode or r2.returncode)
