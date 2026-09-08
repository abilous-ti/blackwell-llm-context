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

1. **Co-authors and the CRediT split.** The paper now carries four authors:

   | Author | Affiliation | ORCID | Email |
   |---|---|---|---|
   | Andriy Bilous (corresponding) | Information Systems and Networks | 0009-0006-5467-7932 | andriy.bilous@uitware.com |
   | Petro Pukach | Applied Mathematics and Fundamental Sciences | 0000-0002-0359-5025 | petro.y.pukach@lpnu.ua |
   | Vasyl Lytvyn | Information Systems and Networks | 0000-0002-9676-0180 | vasyl.v.lytvyn@lpnu.ua |
   | Zoriana Rybchak | Information Systems and Networks | 0000-0002-5986-4618 | zoriana.l.rybchak@lpnu.ua |

   Names, affiliations and ORCIDs were verified against the ORCID public API. **The author
   order and the CRediT split in the manuscript are a drafting placeholder, not a statement
   any co-author has confirmed** - check both with all four before submission. MDPI emails
   every listed co-author to confirm authorship.

2. **Preprint declaration.** MDPI asks whether the manuscript has been posted as a preprint.
   If the arXiv version goes up first, declare it in the cover letter and give the arXiv ID.
   Posting a preprint does not disqualify MDPI submission.

3. **Repository visibility.** The Data Availability Statement points at
   `https://github.com/abilous-ti/blackwell-llm-context`. That repository must be **public**
   before submission or the statement is false and reviewers cannot check any number.

## Outstanding — production format

MDPI's own LaTeX class (`mdpi.cls` + `Definitions/`, `mdpi.bst`) is **not installed here**.
It is not on CTAN and MiKTeX has no `mdpi` package, so it cannot be installed with a package
manager; and `mdpi.com` returns HTTP 403 to non-browser requests, so the zip cannot be fetched
from a script either. Getting it takes a browser: open <https://www.mdpi.com/authors/latex>,
download the zip, unzip it, and the `Definitions/` folder sits next to your `.tex`.
(A community mirror exists on GitHub, but it is unofficial and of unknown vintage - MDPI
production uses the current class, so use the official zip.) The current build uses `article` with MDPI's required
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
