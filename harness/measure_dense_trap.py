"""Do DENSE retrievers / CROSS-ENCODERS mis-rank the trap like lexical cosine does?

Fills the measured middle of the ranker spectrum (lexical falls for the trap; LLM listwise
escapes it): score {W1, W2} against each probe task with production-grade open-weight
rankers and compare the induced ranking with realized PASS.

Models (small, standard, CPU-friendly):
  - BAAI/bge-small-en-v1.5           (dense bi-encoder, BGE family)
  - intfloat/e5-small-v2             (dense bi-encoder, E5 family)
  - cross-encoder/ms-marco-MiniLM-L-6-v2  (cross-encoder reranker)

Deterministic scoring; no sampling needed. Run with the short-path venv python:
  C:/Users/AndriyBilous/stv/Scripts/python.exe tokenbench/measure_dense_trap.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_blackwell import W1, W2, TASKS  # noqa: E402

PROBE = {"trap_store_wire": "W1", "api_post_ok": "W1", "enc_amount": "W2"}  # PASS truth


def main():
    from sentence_transformers import SentenceTransformer, CrossEncoder, util
    tasks = {t["id"]: t["prompt"] for t in TASKS if t["id"] in PROBE}
    out = {}

    def record(model_name, tid, s1, s2):
        pick = "W1" if s1 > s2 else "W2"
        agree = pick == PROBE[tid]
        out.setdefault(model_name, {})[tid] = {
            "score_W1": round(float(s1), 4), "score_W2": round(float(s2), 4),
            "top": pick, "pass_truth": PROBE[tid], "agrees_with_PASS": agree}
        print(f"  {model_name:<38} {tid:<16} W1={s1:+.4f} W2={s2:+.4f} -> {pick} "
              f"[{'AGREE' if agree else 'MIS-RANK'}]", flush=True)

    # ---- dense bi-encoders ----
    for name, qpre, dpre in [("BAAI/bge-small-en-v1.5",
                              "Represent this sentence for searching relevant passages: ", ""),
                             ("intfloat/e5-small-v2", "query: ", "passage: ")]:
        m = SentenceTransformer(name)
        d = m.encode([dpre + W1, dpre + W2], normalize_embeddings=True)
        for tid, tp in tasks.items():
            q = m.encode([qpre + tp], normalize_embeddings=True)
            s = util.cos_sim(q, d)[0]
            record(name, tid, s[0], s[1])

    # ---- cross-encoder ----
    ce_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ce = CrossEncoder(ce_name)
    for tid, tp in tasks.items():
        s1, s2 = ce.predict([(tp, W1), (tp, W2)])
        record(ce_name, tid, s1, s2)

    trap_misranks = [m for m, r in out.items()
                     if not r["trap_store_wire"]["agrees_with_PASS"]]
    print("\nVERDICT:", flush=True)
    if trap_misranks:
        print(f"  MIS-RANK the trap: {trap_misranks} -> the mis-rank extends into the "
              "dense/cross-encoder middle of the spectrum.", flush=True)
    else:
        print("  All dense/cross-encoder rankers get the trap RIGHT -> honest null; "
              "the topical class boundary sits below this family on these probes.",
              flush=True)
    # results/dense_trap.json is the frozen published record, pinned in MANIFEST.md.
    # Writing there by default would replace the paper's evidence before a reviewer could
    # compare against it, so reproductions land beside it and overwriting is explicit.
    import argparse as _ap
    _p = _ap.ArgumentParser()
    _p.add_argument("--out", default=None,
                    help="output path (default: results/reproduce/dense_trap.json)")
    _a, _ = _p.parse_known_args()
    _root = Path(__file__).resolve().parent.parent
    _out = Path(_a.out) if _a.out else _root / "results" / "reproduce" / "dense_trap.json"
    _out.parent.mkdir(parents=True, exist_ok=True)
    _out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote %s" % _out, flush=True)
    if _out.resolve() != (_root / "results" / "dense_trap.json").resolve():
        print("   (the published record at results/dense_trap.json is untouched)", flush=True)


if __name__ == "__main__":
    main()
