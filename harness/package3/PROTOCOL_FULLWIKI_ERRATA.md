# Package 3 protocol: erratum

Written 6 October 2026, after the confirmatory run. `PROTOCOL_FULLWIKI.md` is frozen: its SHA-256,
`0e743e60af3ec0b01d8671794601bea341a4e6abe7050533a88c4e2182dfac58`, is one of the digests in the
package-3 freeze. The file is therefore left unchanged, so its hash still verifies, and the
correction is recorded here. This note is not part of the freeze.

## Section 3, subgroup: the file-wide count of sufficient questions

The protocol says: "In the whole file, 2,089 of the 7,342 eligible questions are sufficient."

The correct count is **2,066 of the 7,342 eligible questions**: these have both supporting titles
among their ten candidates. The figure 2,089 counts the same property over all 7,405 questions of
the file, eligible or not. The draw recorded 2,066 (`counts.all_sufficient` in the sample, also in
`results/package3/confirm_fullwiki_textfree/sample.json`), and
`python harness/package3/verify_fullwiki_textfree.py --rebuilt` recomputes both counts from the
public parquet.

The statement is descriptive. It enters no setting and no rule. The draw, the 300 confirmatory
questions, their subgroup labels (90 sufficient, 210 complement) and every analysis are unaffected.
