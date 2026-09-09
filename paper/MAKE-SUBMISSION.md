# MAKE (MDPI) submission checklist

Target: *Machine Learning and Knowledge Extraction* (MAKE), MDPI.

Build the submission PDF with:

```bash
python paper/build_make_variant.py && pdflatex blackwell-paper-make && bibtex blackwell-paper-make && pdflatex blackwell-paper-make && pdflatex blackwell-paper-make
```

`blackwell-paper-make.tex` is **generated** from `blackwell-paper.tex`. Never hand-edit it —
edit the master and regenerate, or the two will drift.

## Authors, as submitted

Order confirmed by the corresponding author.

| # | Author | Affiliation | ORCID | Email |
|---|---|---|---|---|
| 1 | **Andriy Bilous** (corresponding) | 1 | 0009-0006-5467-7932 | andriy.bilous@uitware.com |
| 2 | Vasyl Lytvyn | 1 | 0000-0002-9676-0180 | vasyl.v.lytvyn@lpnu.ua |
| 3 | Petro Pukach | 2 | 0000-0002-0359-5025 | petro.y.pukach@lpnu.ua |
| 4 | Zoriana Rybchak | 1 | 0000-0002-5986-4618 | zoriana.l.rybchak@lpnu.ua |

1. Department of Information Systems and Networks, Institute of Computer Science and Information
   Technologies, Lviv Polytechnic National University, S. Bandery St. 12, 79013 Lviv, Ukraine
2. Institute of Applied Mathematics and Fundamental Sciences, Lviv Polytechnic National
   University, S. Bandery St. 12, 79013 Lviv, Ukraine

Names, affiliations and ORCIDs were verified against the ORCID public API.

## Manuscript requirements — done

| Requirement | State |
|---|---|
| Title | present; running title not needed until production |
| Author list in MDPI form (`Name 1,*, Name 1, Name 2, …`) | present, with ORCID iDs |
| Numbered affiliations with full postal address | present |
| Corresponding-author line | present |
| Abstract ≤ 200 words | 199 |
| No citations in the abstract | none |
| Keywords (3–10) | 10 |
| Author Contributions (CRediT) | present, reconciled with the commit history; co-author roles to confirm (see below) |
| Commit provenance stated in the manuscript | Data Availability Statement |
| Funding statement | present (no external funding) |
| Institutional Review Board Statement | present (not applicable, reason stated) |
| Informed Consent Statement | present (not applicable) |
| Data Availability Statement | present, points at the artifact repository |
| Acknowledgments | present |
| Use of Generative AI disclosure | present, in Acknowledgments and a dedicated section |
| Frozen manifest of the records | `results/MANIFEST.md`, 3313 files pinned by SHA-256 |
| Conflicts of Interest | present |
| Abbreviations table | present |
| Numbered reference style | `natbib[numbers]` + `unsrtnat` |
| References real, used, and verified | 72 entries, 72 cited, 0 uncited; all 47 arXiv ids resolve with matching titles; DOIs and Zenodo records checked |
| Every reported number recomputed from the raw records | yes, by the scripts in `harness/` |

## Outstanding — author decisions before you press submit

1. **Co-author confirmation, and the authorship-criteria question under it.** The commit
   history is 77 commits, every one authored by A.B.; no co-author committed anything. The
   CRediT paragraph was rewritten to match: every artifact-producing role (software,
   investigation, validation, formal analysis, data curation, visualization, original draft)
   is A.B. alone. The co-authors are left with writing---review and editing (all three),
   supervision (V.L., P.P.) and project administration (V.L.), because a commit log can
   neither evidence nor refute off-repository work.

   **Two things to settle before submitting.** First, if any co-author did contribute to
   conception, design or interpretation through discussion rather than code, say so and
   restore those roles - they were removed for lack of evidence, not because they are known
   to be absent. Second, MDPI applies ICMJE-style criteria: supervision plus review and
   editing alone may not meet "substantial contribution to conception or design, or to
   acquisition, analysis or interpretation". If a co-author's real contribution is only
   supervisory, the correct place for it may be the Acknowledgments rather than the author
   list. This is the corresponding author's call; MDPI emails every listed co-author to
   confirm, so a mismatch surfaces at submission.

2. **The generative-AI disclosure must be checked for accuracy.** The manuscript now states that
   an AI coding assistant was used for the harness, the analysis scripts and parts of the text,
   and that no result was produced by a model acting as author or analyst. Confirm this matches
   what you are willing to declare — MDPI treats a false or missing disclosure as a research
   integrity matter.

3. **Repository visibility.** The Data Availability Statement points at
   `https://github.com/abilous-ti/blackwell-llm-context`. That repository is public as of the
   last push; keep it public, or the statement is false and reviewers cannot check any number.

4. **Preprint declaration.** MDPI asks whether the manuscript has been posted as a preprint. If
   the arXiv version goes up first, declare it in the submission form and the cover letter with
   the arXiv id. Posting a preprint does not disqualify MDPI submission.

5. **Rotate the Azure API key** used for the GPT-5.5, DeepSeek and Kimi runs. It was pasted in
   plain text during development. It is in no tracked file and in no commit, but rotate it.

6. **Optional, the biggest remaining reviewer lever:** prevalence is measured in a companion
   study (16/85 pairs incomparable, 2/36 co-retrieved) but not imported here. The manuscript
   currently declares prevalence unmeasured in `\S`Limitations. Importing it would answer the
   most likely reviewer objection; leaving it out keeps this paper's scope clean. Undecided.

## Outstanding — production format

MDPI's own LaTeX class (`mdpi.cls` + `Definitions/`, `mdpi.bst`) is **not installed here**. It is
not on CTAN and MiKTeX has no `mdpi` package, so it cannot be installed with a package manager;
`mdpi.com` returns 403 to scripted download.

This does not block submission: MAKE accepts a PDF for review, and MDPI's production office
converts the accepted manuscript into their template. `blackwell-paper-make.tex` is built to be
close to that template in the ways that matter for review — MDPI-shaped author block, numbered
references, complete back matter — so the conversion is mechanical.

If you want the true MDPI class before submitting, download the LaTeX template zip manually from
the MAKE "Instructions for Authors" page while logged in, unpack it beside the `.tex`, and swap
`\documentclass{article}` for `\documentclass[make,article,submit,pdftex,moreauthors]{mdpi}`.
The back matter section names in this manuscript already match the macros that template expects.

## Submission package

| File | Purpose |
|---|---|
| `blackwell-paper-make.pdf` | the review PDF |
| `blackwell-paper-make.tex` + `blackwell-paper.bib` | source, if the editor asks for it |
| `blackwell-paper-MAKE.docx` | Word version, if the editor prefers it |
| `COVER-LETTER.md` | cover letter, edit the bracketed fields before sending |
| the artifact repository | referenced by the Data Availability Statement |
