# Cover letter — MAKE submission

*Draft. Fields in [brackets] need a decision before sending. Everything else is factual and
checked against the manuscript.*

---

To the Editors,
*Machine Learning and Knowledge Extraction* (MAKE)

Dear Editors,

We submit **"Context selection as a partial order: A Blackwell framework and verified LLM
evidence"** for consideration as a research article in *Machine Learning and Knowledge
Extraction*.

**What the paper does.** Production systems choose prompt context by scoring each candidate source
with one number and keeping the top few — this is what retrieval-augmented generation, in-context
example selection, and agentic coding tools all do. We argue the scalar is the wrong abstraction
and show why with a classical tool. Modelling a context source as a statistical experiment on what
a task's verifier actually checks, two sources can be *Blackwell-incomparable*: neither is a
garbled copy of the other. When they are, no single per-source score can rank them correctly for
every task, because a score imposes a total order while the truth is partial.

**What is new is the measurement.** The theory is classical and we claim none of it. Our
contribution is to make incomparability an object you can *test* on a live model, and then to test
it. We give a distribution-free verification — exact Clopper–Pearson intervals over a battery of
pass/fail tasks, union-bounded at η = 0.10 — and report:

- verified incomparability of two hand-built sources on **six models across four vendors**, in
  both directions, holding simultaneously at ≥ 90 % after paying for the conjunction;
- a designed trap on which a lexical score, two dense bi-encoders and a cross-encoder all prefer
  the wrong source, while a listwise LLM reranker that reads the deciding detail does not;
- verified **anti-monotonicity**: a strict superset of a sufficient source lowers the pass rate on
  eleven of twelve cells, with padding, order, routing-instruction and structured-context controls.

Every number is an empirical pass rate from live API calls graded by executable verifiers. The
measurement harness, every raw run record, and the scripts that recompute every table are openly
available at <https://github.com/abilous-ti/blackwell-llm-context>.

**Fit with MAKE.** The paper is an extraction-and-selection result about what knowledge a model
can actually use, and it ends in something an engineer can act on: keep the verified non-dominated
set and route by task, rather than force a global top-1. The scope section is explicit about what
is *not* established — prevalence in production retrieval is not measured, the behavioural
controls are single-model, and the selection rule is demonstrated at curation scale, not corpus
scale.

**Declarations.** This manuscript is original, is not under consideration elsewhere, and all four
authors have approved the submission. There is no external funding and no conflict of interest.
The study involved no human participants or animals. Use of generative AI is disclosed in a
dedicated section: language models are the measured *subject* of the study, and an AI coding
assistant was additionally used as a *tool* for the harness, the analysis scripts and parts of the
text, with all reported quantities computed from the released raw records and verified by the
authors. [Preprint: state here whether an arXiv version has been posted, and give the arXiv id.]

We suggest the following as possible reviewers, none of whom has a conflict with the authors:
[list 3–5 names with affiliations and emails, or delete this paragraph — MAKE does not require it].

Thank you for considering our work.

Sincerely,

**Petro Pukach** (corresponding author)
Institute of Applied Mathematics and Fundamental Sciences,
Lviv Polytechnic National University
S. Bandery St. 12, 79013 Lviv, Ukraine
petro.y.pukach@lpnu.ua · ORCID 0000-0002-0359-5025

on behalf of Andriy Bilous, Vasyl Lytvyn and Zoriana Rybchak
