"""(1) trim the abstract under MDPI's 200-word limit;
(2) generate blackwell-paper-make.tex, the MAKE-targeted build: MDPI numeric
    citation style and an MDPI-shaped title block. Generated, never hand-edited,
    so it cannot drift from the master."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\research\out"
P = os.path.join(D, "blackwell-paper.tex")
M = os.path.join(D, "blackwell-paper-make.tex")
NL, BS = chr(10), chr(92)
s = open(P, "rb").read().decode("utf-8").replace("\r\n", "\n")

def words(tex):
    out, i = [], 0
    while i < len(tex):
        ch = tex[i]
        if ch == BS:
            i += 1
            while i < len(tex) and tex[i].isalpha(): i += 1
            out.append(" ")
        elif ch in "{}$~%":
            out.append(" "); i += 1
        else:
            out.append(ch); i += 1
    return [x for x in "".join(out).split() if any(c.isalnum() for c in x)]

# (abstract handled by abs_trim.py; this script only generates the variant)

# ---------------- 2. MAKE variant ------------------------------------------
m = s

def sub(name, old, new, cnt=1):
    global m
    c = m.count(old)
    assert c == cnt, "%s: %d != %d" % (name, c, cnt)
    m = m.replace(old, new)
    print("   ", name)

sub("natbib numeric",
    r"\usepackage{amsmath,amssymb,amsthm,booktabs,hyperref,natbib,microtype,enumitem}",
    r"\usepackage{amsmath,amssymb,amsthm,booktabs,hyperref,microtype,enumitem}" + NL +
    r"\usepackage[numbers,sort&compress]{natbib}  % MDPI uses numbered references")

sub("bibstyle", r"\bibliographystyle{plainnat}", r"\bibliographystyle{unsrtnat}")

sub("header",
    r"%  arXiv article source. All references verified against arXiv/DBLP/publisher",
    r"%  MAKE (MDPI) submission build. GENERATED from blackwell-paper.tex -- do not" + NL +
    r"%  hand-edit; regenerate with scratchpad/make_build.py after editing the master." + NL +
    r"%  Differences from the master: numbered (MDPI) citation style and an MDPI-shaped" + NL +
    r"%  title block with corresponding-author details." + NL +
    r"%  All references verified against arXiv/DBLP/publisher")

sub("title block",
NL.join([
r"\author{%",
r"  Andriy Bilous \\",
r"  Department of Information Systems and Networks \\",
r"  Lviv Polytechnic National University, Lviv, Ukraine \\",
r"  ORCID: 0009-0006-5467-7932 \\",
r"  \texttt{andriy.bilous@uitware.com}",
r"}"]),
NL.join([
r"\author{%",
r"  Andriy Bilous\,$^{1,\ast}$ \\[2pt]",
r"  \normalsize $^{1}$\,Department of Information Systems and Networks, Lviv Polytechnic National"
r" University, \\",
r"  \normalsize S.~Bandery St.~12, 79013 Lviv, Ukraine; \texttt{andriy.bilous@uitware.com} \\[2pt]",
r"  \normalsize ORCID: 0009-0006-5467-7932 \\[2pt]",
r"  \normalsize $^{\ast}$\,Correspondence: \texttt{andriy.bilous@uitware.com}",
r"}",]))

open(M, "w", encoding="utf-8", newline="\n").write(m)
print("written:", M)
