#!/bin/sh
# Build every submission deliverable from the master, and FAIL LOUDLY if any step
# does. The MAKE variant went stale for two commits because this pipeline was run
# with its output suppressed and the generator's assertion never reached anyone.
#
# Usage:  sh paper/build_deliverables.sh
set -e

# Everything is relative to this script and the output stays inside the repository.
# It used to be assembled in a different checkout, which no reviewer has.
REPO=$(cd "$(dirname "$0")/.." && pwd)
OUT="${BLACKWELL_BUILD_DIR:-$REPO/paper/_build}"
mkdir -p "$OUT"
# Tool locations are overridable; the defaults are the usual per-user install paths.
[ -n "$MIKTEX_BIN" ] && PATH="$PATH:$MIKTEX_BIN"
PATH="$PATH:$HOME/AppData/Local/Programs/MiKTeX/miktex/bin/x64"
PANDOC="${PANDOC:-$HOME/AppData/Local/Pandoc/pandoc}"
command -v pdflatex >/dev/null || { echo "pdflatex not found; set MIKTEX_BIN"; exit 1; }

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
# `cmd | tail -1` reports tail's status, so under /bin/sh a failing check reached the
# success message with exit 0. Run each check on its own and test its status.
run_check() {
  out=$("$@") || { echo "CHECK FAILED: $*"; echo "$out" | tail -20; exit 1; }
  echo "$out" | tail -1
}
run_check python harness/diag/check_regimes.py
# A bound printed tighter than the one computed asserts more than the data support. Two rounds
# of review found instances of it, so it is checked here rather than by eye.
run_check python harness/diag/check_printed_bounds.py
echo "ALL DELIVERABLES BUILT"
