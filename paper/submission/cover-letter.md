# Cover letter — draft for the corresponding author

**To:** The Editors, *Machine Learning and Knowledge Extraction* (MAKE)
**Manuscript:** Context selection as a partial order: A Blackwell framework and verified LLM evidence
**Corresponding author:** Petro Pukach (petro.y.pukach@lpnu.ua)
**Article type:** Article

---

Dear Editors,

We submit for your consideration the manuscript "Context selection as a partial order: A Blackwell
framework and verified LLM evidence" as an original research Article.

**What the paper does.** Systems that assemble prompt context almost always score each candidate
source with one number and keep the top few. We ask what such a task-independent scalar ranking can
represent, and answer with the classical apparatus of statistical decision theory. Using Blackwell's
comparison of experiments we prove that when two sources are incomparable, no single per-source
score fixed across tasks ranks them correctly for every decision problem. We then separate that
structural statement from the behaviour of a fixed model, which is what practitioners actually
observe, and give a finite-sample procedure that decides on a live model whether two particular
sources are incomparable — executable verifiers, exact binomial confidence bounds, and an explicit
multiplicity correction.

**Why it is significant.** The impossibility is not a restatement of "relevance is imperfect": it
identifies a structural limit of an entire class of ranking methods, and it comes with an instrument
that tests for the condition on real systems rather than assuming it. Two measured findings sharpen
the point. On a designed relevance trap, a lexical score, two dense retrievers and a cross-encoder
all prefer the less useful source, while a listwise LLM reranker that reads the deciding detail does
not — so the failure tracks what a scorer can see, not how good it is. And adding a second, entirely
correct source to a sufficient one lowers pass rates, with observed collapses from 100% to 0% and
eleven of twelve tested contrasts clearing a 30-percentage-point harm margin under joint 90%
confidence control. That is a verified counterexample to the intuition that more correct context
cannot hurt, and it constrains any selection policy that concatenates retained candidates.

**Fit to the journal's scope.** The work sits where MAKE's scope places knowledge extraction and
machine learning together: it concerns how knowledge is selected and delivered to a learned system,
gives the selection problem a formal object, and validates it empirically on deployed models. Six
models from four vendors are measured under one protocol, with all controls published.

**Reproducibility.** Every number in the manuscript is computed by released scripts from released
measurement records. The repository pins each record by SHA-256 in a manifest that maps every table
and figure to the files it is computed from, and the build verifies that each printed confidence
bound is implied by the computed one. We report the negative and unverified results alongside the
verified ones, including a control that does not separate and a mechanism the record does not
establish.

**Limitations we state plainly.** The findings establish existence on a constructed coding battery,
not prevalence in natural retrieval traffic, and we do not claim an implementable selector with
demonstrated gains on unseen tasks. We also note that the Blackwell–Le Cam apparatus reached
inference-time context selection concurrently with this work, from a different direction, and we
claim no priority over it; the relevant work is cited and discussed.

We confirm that neither the manuscript nor any parts of its content are currently under
consideration for publication with or published in another journal.

All authors have approved the manuscript and agree with its submission to MAKE.

Yours sincerely,

Petro Pukach, on behalf of Andriy Bilous, Vasyl Lytvyn, Petro Pukach and Zoriana Rybchak
Lviv Polytechnic National University, Lviv, Ukraine

---

## Notes for the corresponding author — delete before sending

- The two statements above are **required verbatim** by MAKE's Instructions for Authors. Confirm
  both are true before sending; they are assertions only an author can make.
- Proposed and excluded reviewer names go **in the submission system, not in this letter**.
- If the manuscript was previously submitted to any MDPI journal, that must be acknowledged and the
  previous manuscript ID given in the submission system.
- Check whether Lviv Polytechnic participates in MDPI's Institutional Open Access Program; the APC
  is CHF 1800 on acceptance and IOAP membership carries a discount.
