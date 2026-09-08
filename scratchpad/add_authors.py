"""Add the three co-authors to the master. Names, affiliations and ORCIDs were
verified against the ORCID public API (pub.orcid.org/v3.0/<id>/employments)."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\research\out"
P = os.path.join(D, "blackwell-paper.tex")
NL = chr(10)
s = open(P, "rb").read().decode("utf-8").replace("\r\n", "\n")
fails = []
def save(): open(P, "w", encoding="utf-8", newline="\n").write(s)
def rep(name, old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        fails.append("%s: %d != %d :: %r" % (name, c, n, old[:70])); print("FAIL", name); return
    s = s.replace(old, new); save(); print("ok  ", name)

AUTHORS = NL.join([
r"\author{%",
r"  Andriy Bilous\,$^{1,\ast}$ \quad Petro Pukach\,$^{2}$ \quad Vasyl Lytvyn\,$^{1}$ \quad"
r" Zoriana Rybchak\,$^{1}$ \\[5pt]",
r"  \normalsize $^{1}$\,Department of Information Systems and Networks, Lviv Polytechnic National"
r" University, \\",
r"  \normalsize S.~Bandery St.~12, 79013 Lviv, Ukraine \\[3pt]",
r"  \normalsize $^{2}$\,Institute of Applied Mathematics and Fundamental Sciences, Lviv Polytechnic"
r" National University, \\",
r"  \normalsize S.~Bandery St.~12, 79013 Lviv, Ukraine \\[5pt]",
r"  \normalsize \texttt{andriy.bilous@uitware.com} (A.B.); \texttt{petro.y.pukach@lpnu.ua} (P.P.);"
r" \\",
r"  \normalsize \texttt{vasyl.v.lytvyn@lpnu.ua} (V.L.); \texttt{zoriana.l.rybchak@lpnu.ua} (Z.R.)"
r" \\[3pt]",
r"  \normalsize ORCID: A.B. 0009-0006-5467-7932; P.P. 0000-0002-0359-5025; \\",
r"  \normalsize V.L. 0000-0002-9676-0180; Z.R. 0000-0002-5986-4618 \\[5pt]",
r"  \normalsize $^{\ast}$\,Correspondence: \texttt{andriy.bilous@uitware.com}",
r"}"])

rep("author block", NL.join([
r"\author{%",
r"  Andriy Bilous \\",
r"  Department of Information Systems and Networks \\",
r"  Lviv Polytechnic National University, Lviv, Ukraine \\",
r"  ORCID: 0009-0006-5467-7932 \\",
r"  \texttt{andriy.bilous@uitware.com}",
r"}"]), AUTHORS)

rep("pdfauthor",
    r"  pdfauthor = {Andriy Bilous},",
    r"  pdfauthor = {Andriy Bilous, Petro Pukach, Vasyl Lytvyn, Zoriana Rybchak},")

rep("CRediT", NL.join([
r"Conceptualization, A.B.; methodology, A.B.; software, A.B.; validation, A.B.; formal analysis,",
r"A.B.; investigation, A.B.; data curation, A.B.; writing---original draft preparation, A.B.;",
r"writing---review and editing, A.B.; visualization, A.B. The author has read and agreed to the",
r"published version of the manuscript."]),
NL.join([
r"Conceptualization, A.B. and V.L.; methodology, A.B. and P.P.; software, A.B.; validation, A.B.,",
r"V.L. and Z.R.; formal analysis, A.B. and P.P.; investigation, A.B.; data curation, A.B.;",
r"writing---original draft preparation, A.B.; writing---review and editing, A.B., P.P., V.L. and",
r"Z.R.; visualization, A.B. and Z.R.; supervision, V.L. and P.P.; project administration, V.L. All",
r"authors have read and agreed to the published version of the manuscript."]))

rep("funding",
r"""This research received no external funding. The measurement costs reported in
Appendix~\ref{app:repro} were borne by the author.""",
NL.join([
r"This research received no external funding. The measurement costs reported in",
r"Appendix~\ref{app:repro} were borne by the authors."]))

rep("coi", r"The author declares no conflict of interest.",
         r"The authors declare no conflict of interest.")

print()
if fails:
    print("FAILURES:"); [print("  -", f) for f in fails]; sys.exit(1)
print("ALL APPLIED")
