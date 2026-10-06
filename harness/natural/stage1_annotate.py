r"""Stage 1 audit record: the manual judgments on the 40 sampled items, with the HotpotQA
single-paragraph questions written for the source-pair design, and automated checks of them.

Each TAT-QA question and each HotpotQA single-paragraph question gets a verdict:
  keep      measures the intended single-source task with a deterministic answer;
  keep-f1   keep, but the gold answer is a long span that exact match cannot score;
  exclude   with the reason (ambiguous, ill-posed, gold unsupported, sign ambiguity, ...).
'leak' marks items whose answer a model may well know without any context; the Stage 2
no-context condition measures this, it is not decided here.

Writes natural_data/stage1/audit.json and prints the summary used in STAGE1-REPORT.md.
Usage:  python harness/natural/stage1_annotate.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S1 = os.path.join(ROOT, "natural_data", "stage1")

# ---- TAT-QA verdicts: (table-only, text-only, table-text) per sampled document -----------------
TAT = {
    0: ("keep", "keep-f1", "keep"), 1: ("keep", "exclude: ill-posed (gold is a context-specific role, not what Lamb Weston is)", None),
    2: ("keep", "keep-f1", "keep"), 3: ("keep", "keep-f1", "keep"),
    4: ("exclude: ambiguous sign (both changes negative; gold assumes magnitude)", "keep-f1", "keep"),
    5: ("exclude: ambiguous sign and wrong scale annotation", "keep", "keep"),
    6: ("keep", "keep-f1", "keep: answerable from the table alone"), 7: ("keep", "keep-f1", None),
    8: ("keep", "keep: table holds a confusable figure (5) beside the text's 1 million", "keep"),
    9: ("keep", "keep-f1", "keep"), 10: ("keep", "exclude: meta question about the table", "keep"),
    11: ("keep", "keep-f1", None), 12: ("keep", "keep", "keep"), 13: ("keep", "keep-f1", None),
    14: ("exclude: sign ambiguity (costs shown negative, gold positive)", "keep-f1", None),
    15: ("keep", "keep", None), 16: ("keep", "keep-f1", None), 17: ("keep", "keep", None),
    18: ("keep", "keep", None), 19: ("keep: multi-span in order", "keep", None),
}

# ---- HotpotQA: single-paragraph questions (P1 = first gold title, P2 = second) ----------------
HOT = {
    0: {"sq": [("In which province is Siping?", ["Jilin"]), ("In which province is Linhai?", ["Zhejiang"])],
        "orig": "keep", "note": "leak: Siping's title names its province; both cities well known"},
    1: {"sq": [("How many members did The Futureheads have?", ["4", "four"]), ("How many members does Marcy Playground have?", ["3", "three"])],
        "orig": "keep", "note": "P1 count must be counted from four names"},
    2: {"sq": [("When was Ulf Merbold born?", ["June 20, 1941"]), ("When was Miroslaw Hermaszewski born?", ["September 15, 1941"])],
        "orig": "keep", "note": "confusable dates, same year: a strong interference probe"},
    3: {"sq": None, "orig": "exclude: 'musician' must be inferred from 'singer, songwriter'; professions are multi-valued",
        "note": "no deterministic single-paragraph question"},
    4: {"sq": [("Which country is the band Fireflight from?", ["United States", "America", "American", "USA", "U.S."]),
               ("Which country is the band Dirty Pretty Things from?", ["England", "English", "United Kingdom", "UK"])],
        "orig": "keep", "note": "confusable nationality"},
    5: {"sq": [("In what year was Leopold Lummerstorfer born?", ["1968"]), ("When was Laurent Touil-Tartour born?", ["November 23, 1971"])],
        "orig": "keep", "note": "obscure people: low closed-book risk; confusable birth dates"},
    6: {"sq": [("What genre of band was 13 Engines?", ["alternative rock"]), ("What genre of band was Oingo Boingo?", ["new wave"])],
        "orig": "keep", "note": "Oingo Boingo widely known"},
    7: {"sq": [("In what year was the Dick Smith Super-80 presented in Electronics Australia magazine?", ["1981"]),
               ("In what year was the Pecom 32 developed?", ["1985"])],
        "orig": "keep", "note": "confusable years"},
    8: {"sq": None, "orig": "exclude: gold not supported (no passenger count for Palm Springs in its passage)",
        "note": "gold also doubtful on the facts"},
    9: {"sq": [("Which company was Cars 2 produced for?", ["Walt Disney Pictures", "Disney"]),
               ("For which company's film soundtrack did Lin-Manuel Miranda co-write songs?", ["Disney"])],
        "orig": "keep", "note": "alias handling needed (Disney, Walt Disney Pictures, Pixar)"},
    10: {"sq": [("Which stunt performer's craze did the game Stunt Cycle try to cash in on?", ["Evel Knievel"]),
                ("When was Evel Knievel born?", ["October 17, 1938"])],
         "orig": "keep", "note": "leak: famous entity"},
    11: {"sq": None, "orig": "keep", "note": "first paragraph lists six neighbours (no single answer); leak: common geography"},
    12: {"sq": [("Which hijacked flight was Heather Penney ordered to ram?", ["United Airlines Flight 93", "Flight 93"]),
                ("Where did United Airlines Flight 93 crash?", ["Somerset County, Pennsylvania", "Pennsylvania"])],
         "orig": "keep", "note": "leak: famous event"},
    13: {"sq": [("The Dry Tortugas lie 60 miles west of which city?", ["Key West"]),
                ("What is the official city motto of Key West?", ["One Human Family"])],
         "orig": "keep", "note": "leak: P1 fact common knowledge"},
    14: {"sq": [("In what year did Glazunov begin his Symphony No. 9?", ["1910"]),
                ("During which years was Glazunov director of the Saint Petersburg Conservatory?", ["1905 and 1928", "1905-1928", "1905 to 1928"])],
         "orig": "keep-f1", "note": "original answer is a clause"},
    15: {"sq": [("In which 2017 television series did Li Yitong play Huang Rong?", ["Legend of the Condor Heroes"]),
                ("On which network did The Legend of the Condor Heroes (2017) start airing in mainland China?", ["Dragon TV"])],
         "orig": "keep", "note": "obscure: low closed-book risk"},
    16: {"sq": [("Who adopted Jeremiah Porter in 2015?", ["Glenn Cook"]), ("When was the actor Ben Cook born?", ["December 11, 1997"])],
         "orig": "exclude: malformed (Ben Cook is Porter's adoptive brother, not his son)",
         "note": "single-paragraph questions are sound"},
    17: {"sq": [("At which two battles of 1813 did Gorchakov command the 1st Infantry Corps?", ["Dresden and Leipzig"]),
                ("When was the Battle of Dresden fought?", ["26-27 August 1813", "26–27 August 1813", "August 1813"])],
         "orig": "exclude: ambiguous (Leipzig is also a major Napoleonic engagement)", "note": "P1 answer is two-valued"},
    18: {"sq": [("Which band recorded the song Stinkfist?", ["Tool"]),
                ("On what date was the album AEnima released in vinyl format?", ["September 17, 1996"])],
         "orig": "keep", "note": "leak: famous band"},
    19: {"sq": [("Who hosted the 1948 Commonwealth Prime Ministers' Conference?", ["Clement Attlee", "Attlee"]),
                ("Which political party did Clement Attlee lead?", ["Labour", "Labour Party"])],
         "orig": "keep", "note": "leak: famous politician"},
}


def norm(s):
    s = s.lower().replace("æ", "ae").replace("ł", "l").replace("–", "-")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s\-]", " ", s)).strip()


def main():
    s = json.load(open(os.path.join(S1, "sample.json"), encoding="utf-8"))
    out = {"tatqa": [], "hotpotqa": []}
    tally = {"tatqa": {}, "hotpotqa": {}}
    for k, it in enumerate(s["tatqa"]):
        for kind, verdict in zip(("table", "text", "table-text"), TAT[k]):
            q = it["questions"].get(kind)
            if q is None:
                continue
            assert verdict is not None, (k, kind)
            out["tatqa"].append({"item": "T%02d" % k, "kind": kind, "uid": q["uid"], "question": q["question"],
                                 "answer": q["answer"], "scale": q["scale"], "verdict": verdict})
            key = "%s:%s" % (kind, verdict.split(":")[0])
            tally["tatqa"][key] = tally["tatqa"].get(key, 0) + 1
    for k, it in enumerate(s["hotpotqa"]):
        a = HOT[k]
        p = [it["paragraphs"][t] for t in it["gold_titles"]]
        rec = {"item": "H%02d" % k, "id": it["id"], "type": it["type"], "question": it["question"], "answer": it["answer"],
               "original_verdict": a["orig"], "note": a["note"], "subquestions": []}
        for j, sq in enumerate(a["sq"] or []):
            q, aliases = sq
            own = any(norm(x) in norm(p[j]) for x in aliases)
            other = any(norm(x) in norm(p[1 - j]) for x in aliases)
            if own and not other:
                verdict = "keep"
            elif other and it["type"] == "bridge" and j == 0:
                verdict = "exclude: hop-1 answer is the other paragraph's subject, so it is guessable from it"
            elif other and k == 9:
                verdict = "exclude: both answers are Disney, so the pair cannot separate the sources"
            elif other:
                verdict = "exclude: answer also in the other paragraph"
            else:
                verdict = "check: answer not found verbatim in its paragraph"
            rec["subquestions"].append({"source": "P%d" % (j + 1), "question": q, "aliases": aliases,
                                        "in_own": own, "in_other": other, "verdict": verdict})
            tally["hotpotqa"]["sub:" + verdict.split(":")[0]] = tally["hotpotqa"].get("sub:" + verdict.split(":")[0], 0) + 1
        tally["hotpotqa"]["orig:" + a["orig"].split(":")[0]] = tally["hotpotqa"].get("orig:" + a["orig"].split(":")[0], 0) + 1
        tally["hotpotqa"]["leak-noted"] = tally["hotpotqa"].get("leak-noted", 0) + ("leak" in a["note"])
        out["hotpotqa"].append(rec)
    pairs = [r for r in out["hotpotqa"] if len(r["subquestions"]) == 2 and all(q["verdict"] == "keep" for q in r["subquestions"])]
    tally["hotpotqa"]["pairs with both single-paragraph questions kept"] = len(pairs)
    tally["hotpotqa"]["of which comparison"] = sum(r["type"] == "comparison" for r in pairs)
    tally["hotpotqa"]["of which noted as leak risk"] = sum("leak" in r["note"] for r in pairs)
    json.dump(out, open(os.path.join(S1, "audit.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    print(json.dumps(tally, indent=1))
    for r in out["hotpotqa"]:
        for sq in r["subquestions"]:
            if sq["verdict"] != "keep":
                print(r["item"], sq["source"], sq["verdict"], "|", sq["question"])


if __name__ == "__main__":
    main()
