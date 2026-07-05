"""Does a LEARNED (LLM listwise) reranker mis-rank the trap like lexical cosine does?

Answers the strongest form of the "bag-of-words is a strawman" critique: rank {W1, W2}
for each task with an LLM listwise reranker (RankGPT-style: the model sees the task and
BOTH candidate documents and orders them), the strongest query-conditioned ranker family
in practice. Position bias is controlled by running both presentation orders.

Ground truth (realized PASS, certified record): trap_store_wire W1>>W2 (the trap:
lexical relevance says W2>W1); api_post_ok W1>>W2 (honest, relevance agrees);
enc_amount W2>>W1 (honest, relevance agrees).

Usage: python tokenbench/measure_reranker_trap.py --n 10 --model claude-haiku-4-5-20251001
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tokenbench.measure_blackwell import W1, W2, TASKS, claude_cmd  # noqa: E402

RERANK_TASKS = ["trap_store_wire", "api_post_ok", "enc_amount"]
GROUND_TRUTH = {"trap_store_wire": "W1", "api_post_ok": "W1", "enc_amount": "W2"}

PROMPT = (
    "You are a retrieval reranker for a coding assistant. Given a coding task and two "
    "candidate context documents, rank the documents by how useful each would be as "
    "context for solving the task. Reply with ONLY a JSON object of the form "
    '{{"ranking": ["A", "B"]}} ordering the document ids from most to least useful. '
    "No prose.\n\nTASK:\n{task}\n\nDOCUMENT A:\n{doc_a}\n\nDOCUMENT B:\n{doc_b}"
)


def rank_once(task_prompt, doc_a, doc_b, model):
    """One reranker call; returns 'A' or 'B' (top-ranked id) or None on parse failure."""
    p = PROMPT.format(task=task_prompt, doc_a=doc_a, doc_b=doc_b)
    cmd = claude_cmd(["-p", " ".join(p.split()), "--model", model,
                      "--output-format", "json", "--max-turns", "1",
                      "--dangerously-skip-permissions"])
    last = None
    for attempt in range(3):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                               timeout=200)
            out = json.loads((r.stdout or "").strip().splitlines()[-1])
            text = out.get("result", "") or ""
            m = re.search(r"\{[^{}]*\"ranking\"[^{}]*\}", text, re.S)
            top = json.loads(m.group(0))["ranking"][0].strip().upper()
            if top in ("A", "B"):
                return top
            raise ValueError(f"bad top id {top!r}")
        except Exception as e:  # transient transport or parse issue -> retry
            last = e
            import time
            time.sleep(5 * (attempt + 1))
    print(f"    [WARN] rank_once failed 3x: {last}", flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="judgments per (task, order)")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--out", default="tokenbench/reranker_trap.json")
    a = ap.parse_args()

    tasks = {t["id"]: t for t in TASKS}
    results = {}
    print(f"LLM listwise reranker probe | model={a.model} | n={a.n} per order "
          f"| tasks={RERANK_TASKS}", flush=True)
    for tid in RERANK_TASKS:
        tp = tasks[tid]["prompt"]
        tally = {"W1_first": 0, "W2_first": 0, "null": 0, "by_order": {}}
        for order in ("W1A", "W1B"):
            doc_a, doc_b = (W1, W2) if order == "W1A" else (W2, W1)
            o = {"W1": 0, "W2": 0, "null": 0}
            for i in range(a.n):
                top = rank_once(tp, doc_a, doc_b, a.model)
                if top is None:
                    o["null"] += 1
                else:
                    winner = ("W1" if top == "A" else "W2") if order == "W1A" else \
                             ("W2" if top == "A" else "W1")
                    o[winner] += 1
            tally["by_order"][order] = o
            tally["W1_first"] += o["W1"]; tally["W2_first"] += o["W2"]
            tally["null"] += o["null"]
            print(f"  {tid:<16} order={order}  W1-top {o['W1']}/{a.n}  "
                  f"W2-top {o['W2']}/{a.n}  null {o['null']}", flush=True)
        n_ok = tally["W1_first"] + tally["W2_first"]
        top_pick = "W1" if tally["W1_first"] >= tally["W2_first"] else "W2"
        agree = top_pick == GROUND_TRUTH[tid]
        tally["reranker_top"] = top_pick
        tally["pass_truth"] = GROUND_TRUTH[tid]
        tally["agrees_with_PASS"] = agree
        results[tid] = tally
        print(f"  {tid:<16} POOLED W1-top {tally['W1_first']}/{n_ok}  ->  reranker says "
              f"{top_pick}, realized PASS says {GROUND_TRUTH[tid]}  "
              f"[{'AGREE' if agree else 'MIS-RANK'}]", flush=True)

    trap = results["trap_store_wire"]
    print("\nVERDICT:", flush=True)
    if not trap["agrees_with_PASS"]:
        print("  The LLM listwise reranker MIS-RANKS the trap like lexical cosine -> the "
              "mis-rank generalizes beyond bag-of-words.", flush=True)
    else:
        print("  The LLM listwise reranker gets the trap RIGHT -> honest null; the "
              "mis-rank claim stays scoped to lexical relevance.", flush=True)
    Path(a.out).write_text(json.dumps(
        {"model": a.model, "n_per_order": a.n, "results": results}, indent=1),
        encoding="utf-8")
    print(f"wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
