r"""Stage 1 of the natural-data evaluation: draw the audit sample and run the automated checks.

TAT-QA (dev): a source pair is one report's TABLE and its TEXT (paragraphs). From the documents
that have at least one question answerable from the table alone and one from the text alone, 20
are drawn; each contributes one table-only question, one text-only question and, where present,
one table-text question (which needs both sources).

HotpotQA (dev, distractor setting): a source pair is a question's two gold paragraphs. Twenty
questions are drawn, ten 'comparison' and ten 'bridge'; their single-paragraph sub-questions are
written and audited by hand in stage1_annotate.py.

Automated check (TAT-QA): which source contains the answer (spans) or the derivation's operands
(arithmetic and counts). A question meant for one source whose evidence also appears in the
other is flagged, because the other source could then answer it too.

Writes natural_data/stage1/sample.json and prints a compact view for the manual audit.
Usage:  python harness/natural/stage1_sample.py
"""
import io
import json
import os
import random
import re
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "natural_data")
OUT = os.path.join(DATA, "stage1")
SEED = 20261002


def numbers(s):
    """Numbers in a string, normalized: thousands separators and signs dropped, '(1,234)' -> 1234."""
    return {n.replace(",", "").lstrip("0") or "0" for n in re.findall(r"\d[\d,]*\.?\d*", str(s))}


def norm(s):
    return re.sub(r"\s+", " ", str(s).lower()).strip()


def table_text(rows):
    return "\n".join(" | ".join(c.strip() for c in r) for r in rows)


def tatqa_evidence(q, table, text):
    """Where the evidence for q is found: (in_table, in_text)."""
    if q["answer_type"] in ("span", "multi-span"):
        spans = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
        in_tab = all(norm(sp) in norm(table) for sp in spans)
        in_txt = all(norm(sp) in norm(text) for sp in spans)
        return in_tab, in_txt
    ops = numbers(q["derivation"]) or numbers(q["answer"])
    tab_n, txt_n = numbers(table), numbers(text)
    return bool(ops) and ops <= tab_n, bool(ops) and ops <= txt_n


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(SEED)
    # ---- TAT-QA ----
    docs = json.load(open(os.path.join(DATA, "tatqa_dataset_dev.json"), encoding="utf-8"))
    eligible = [d for d in docs if {"table", "text"} <= {q["answer_from"] for q in d["questions"]}]
    tat = []
    for d in rng.sample(eligible, 20):
        table = table_text(d["table"]["table"])
        text = "\n\n".join(p["text"] for p in sorted(d["paragraphs"], key=lambda p: p["order"]))
        item = {"doc_uid": d["table"]["uid"], "table": table, "text": text, "questions": {}}
        for kind in ("table", "text", "table-text"):
            pool = [q for q in d["questions"] if q["answer_from"] == kind]
            if pool:
                q = rng.choice(pool)
                in_tab, in_txt = tatqa_evidence(q, table, text)
                item["questions"][kind] = {k: q[k] for k in ("uid", "question", "answer", "derivation",
                                                             "answer_type", "scale", "rel_paragraphs")}
                item["questions"][kind]["evidence_in_table"] = in_tab
                item["questions"][kind]["evidence_in_text"] = in_txt
        tat.append(item)
    # ---- HotpotQA ----
    h = pd.read_parquet(os.path.join(DATA, "hotpot_dev_distractor.parquet"))
    hot = []
    for kind in ("comparison", "bridge"):
        sub = h[h["type"] == kind]
        for i in rng.sample(range(len(sub)), 10):
            r = sub.iloc[i]
            titles = list(r["context"]["title"])
            sents = [list(s) for s in r["context"]["sentences"]]
            gold = list(dict.fromkeys(r["supporting_facts"]["title"]))
            paras = {t: "".join(sents[titles.index(t)]) for t in gold}
            sup = {}
            for t, sid in zip(r["supporting_facts"]["title"], r["supporting_facts"]["sent_id"]):
                sup.setdefault(t, []).append(sents[titles.index(t)][int(sid)] if int(sid) < len(sents[titles.index(t)]) else "<missing sentence>")
            hot.append({"id": r["id"], "type": kind, "question": r["question"], "answer": r["answer"],
                        "gold_titles": gold, "paragraphs": paras, "supporting": sup,
                        "distractor_titles": [t for t in titles if t not in gold]})
    json.dump({"seed": SEED, "tatqa": tat, "hotpotqa": hot}, open(os.path.join(OUT, "sample.json"), "w",
              encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    # ---- compact view ----
    print("TAT-QA: %d eligible documents of %d; 20 drawn" % (len(eligible), len(docs)))
    for k, it in enumerate(tat):
        print("\n[T%02d] %s  table %d rows, text %d chars" % (k, it["doc_uid"][:8], it["table"].count("\n") + 1, len(it["text"])))
        for kind, q in it["questions"].items():
            flag = ""
            if kind == "table" and q["evidence_in_text"]:
                flag = "  <-- evidence also in TEXT"
            if kind == "text" and q["evidence_in_table"]:
                flag = "  <-- evidence also in TABLE"
            if kind != "table-text" and not (q["evidence_in_table"] or q["evidence_in_text"]):
                flag = "  <-- evidence not located automatically"
            print("  %-10s %-10s Q: %s | A: %s %s | deriv: %s%s" % (kind, q["answer_type"], q["question"][:110],
                  str(q["answer"])[:60], q["scale"], str(q["derivation"])[:50], flag))
    print("\nHotpotQA: 10 comparison + 10 bridge drawn")
    for k, it in enumerate(hot):
        print("\n[H%02d] %s | Q: %s | A: %s" % (k, it["type"], it["question"], it["answer"]))
        for t in it["gold_titles"]:
            print("   [%s] supporting: %s" % (t, " ".join(it["supporting"][t])[:260]))


if __name__ == "__main__":
    main()
