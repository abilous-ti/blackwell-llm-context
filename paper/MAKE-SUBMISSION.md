# MAKE (MDPI) submission checklist

Target: *Machine Learning and Knowledge Extraction* (MAKE), MDPI.

Build the submission files with:

```bash
python scratchpad/make_build.py     # regenerates blackwell-paper-make.tex from the master
pdflatex blackwell-paper-make && bibtex blackwell-paper-make && pdflatex blackwell-paper-make && pdflatex blackwell-paper-make
```

`blackwell-paper-make.tex` is **generated** from `blackwell-paper.tex`. Never hand-edit it —
edit the master and regenerate, or the two will drift.

## Done

| Requirement | State |
|---|---|
| Abstract ≤ 200 words | 198 |
| No citations in the abstract | none |
| Keywords (3–10) | 10 |
| Author Contributions (CRediT) | present, single author |
| Funding statement | present |
| Institutional Review Board Statement | present (not applicable, stated why) |
| Informed Consent Statement | present (not applicable) |
| Data Availability Statement | present, points at the artifact repository |
| Conflicts of Interest | present |
| Abbreviations table | present |
| Numbered reference style | `natbib[numbers]` + `unsrtnat` |
| Corresponding-author block | present |
| References real and used | 69 entries, 69 cited, all verified against arXiv/DBLP/Crossref |

## Outstanding — author decisions

1. **Co-author.** The Author Contributions block previously credited a second author
   (initials `O.R.`) who does not appear on the title page. CRediT has been made consistent
   with the single-author title page. If a co-author is to be added, update **both** the
   `\author{}` block (name, affiliation, ORCID) and the CRediT split, and MDPI will ask for
   the co-author's email at submission.

2. **Preprint declaration.** MDPI asks whether the manuscript has been posted as a preprint.
   If the arXiv version goes up first, declare it in the cover letter and give the arXiv ID.
   Posting a preprint does not disqualify MDPI submission.

3. **Repository visibility.** The Data Availability Statement points at
   `https://github.com/abilous-ti/blackwell-llm-context`. That repository must be **public**
   before submission or the statement is false and reviewers cannot check any number.

## Outstanding — production format

MDPI's own LaTeX class (`mdpi.cls` + `Definitions/`, `mdpi.bst`) is **not installed here** and
cannot be fetched from this environment. The current build uses `article` with MDPI's required
content and a numbered reference style, which is acceptable for **peer review** — MDPI accepts
a PDF at submission — but the final production version must be moved onto their template.

When you do convert:

- download the LaTeX template from <https://www.mdpi.com/authors/latex>;
- move the body into `mdpi.cls` with `\documentclass[make,article,submit,pdftex,moreauthors]{Definitions/mdpi}`;
- MDPI's class defines its own `\Author`, `\address`, `\corres`, `\abstract`, `\keyword` macros —
  the front matter here maps onto them one-to-one;
- switch `\bibliographystyle{unsrtnat}` to `mdpi.bst`;
- theorem environments: `mdpi.cls` predefines `Theorem`, `Lemma`, `Proposition`, `Remark`,
  `Definition` (capitalised); the `\newtheorem` block in the preamble is then redundant.

Alternatively submit the Word file (`blackwell-paper-MAKE.docx`) on MDPI's Word template — MAKE
accepts either.

## Files

| File | Purpose |
|---|---|
| `blackwell-paper.tex` | master; arXiv build (author–year references) |
| `blackwell-paper-make.tex` | generated MAKE build (numbered references, MDPI front matter) |
| `blackwell-paper-make.pdf` | submission PDF, 40 pp |
| `blackwell-paper-MAKE.docx` | Word version for MDPI's Word template route |
