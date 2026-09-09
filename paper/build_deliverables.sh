#!/bin/sh
# Build every submission deliverable from the master, and FAIL LOUDLY if any step
# does. The MAKE variant went stale for two commits because this pipeline was run
# with its output suppressed and the generator's assertion never reached anyone.
#
# Usage:  sh paper/build_deliverables.sh
set -e

REPO=/c/Users/AndriyBilous/Documents/GitHub/blackwell-llm-context
OUT=/c/Users/AndriyBilous/Documents/GitHub/tokenguard/research/out
PATH="$PATH:/c/Users/AndriyBilous/AppData/Local/Programs/MiKTeX/miktex/bin/x64"
PANDOC=/c/Users/AndriyBilous/AppData/Local/Pandoc/pandoc

cd "$REPO/paper"

echo "== master"
pdflatex -interaction=nonstopmode blackwell-paper.tex > /dev/null
bibtex blackwell-paper > /dev/null
pdflatex -interaction=nonstopmode blackwell-paper.tex > /dev/null
pdflatex -interaction=nonstopmode blackwell-paper.tex > /dev/null
grep -q '^!' blackwell-paper.log && { echo "TeX ERROR in the master:"; grep -A3 '^!' blackwell-paper.log; exit 1; }
# a duplicate \label silently repoints every ef to the LAST definition, so the paper
# still compiles cleanly while cross-references land in the wrong section. Fail on it.
for L in blackwell-paper.log blackwell-paper-make.log; do
  [ -f "$L" ] || continue
  grep -q 'multiply defined' "$L" && { echo "DUPLICATE LABEL in $L:"; grep 'multiply defined' "$L"; exit 1; }
  grep -qi 'undefined \(reference\|citation\|control sequence\)' "$L" && { echo "UNDEFINED in $L:"; grep -i 'undefined' "$L"; exit 1; }
done
echo "   $(grep -o 'Output written.*pages[^)]*' blackwell-paper.log)"

echo "== MAKE variant"
cp blackwell-paper.tex blackwell-paper.bib "$OUT/"
cd "$OUT"
python "$REPO/paper/build_make_variant.py"          # NOT silenced: it asserts
pdflatex -interaction=nonstopmode blackwell-paper-make.tex > /dev/null
bibtex blackwell-paper-make > /dev/null
pdflatex -interaction=nonstopmode blackwell-paper-make.tex > /dev/null
pdflatex -interaction=nonstopmode blackwell-paper-make.tex > /dev/null
grep -q '^!' blackwell-paper-make.log && { echo "TeX ERROR in the MAKE variant:"; exit 1; }
echo "   $(grep -o 'Output written.*pages[^)]*' blackwell-paper-make.log)"

echo "== DOCX"
python "$REPO/paper/build_make_docx.py"
"$PANDOC" _make_docx_tmp.tex --bibliography=blackwell-paper.bib --citeproc \
          -o blackwell-paper-MAKE.docx

cp blackwell-paper-make.tex blackwell-paper-make.pdf blackwell-paper-MAKE.docx "$REPO/paper/"

echo "== drift check"
cd "$REPO"
python - <<'EOF'
import sys
m = open("paper/blackwell-paper.tex", encoding="utf-8").read()
v = open("paper/blackwell-paper-make.tex", encoding="utf-8").read()
# the variant differs from the master only in the citation package, the bib style
# and the header comment; every other line must be present in both.
bad = [l for l in m.split("\n")
       if l.strip() and not l.lstrip().startswith("%")
       and "natbib" not in l and "bibliographystyle" not in l
       and l not in v]
if bad:
    print("DRIFT: %d master lines missing from the MAKE variant, e.g." % len(bad))
    for l in bad[:5]:
        print("   ", l[:100])
    sys.exit(1)
print("   variant matches the master")
EOF

echo "== verification"
python harness/diag/check_regimes.py | tail -1
echo "ALL DELIVERABLES BUILT"
