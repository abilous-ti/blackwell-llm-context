r"""Local rankers over each question's own candidate pool (no API calls).

  bm25    Okapi BM25 (k1 = 1.5, b = 0.75), IDF over every paragraph of the source dataset
  bge     BAAI/bge-small-en-v1.5 bi-encoder, with its retrieval query instruction
  e5      intfloat/e5-small-v2 bi-encoder ('query: ' / 'passage: ' prefixes)
  minilm  cross-encoder/ms-marco-MiniLM-L-6-v2 cross-encoder
  mmr     maximal marginal relevance (Carbonell and Goldstein, 1998) on the bge embeddings,
          lambda = 0.5 fixed in advance (a common library default), greedy over the whole pool

The three checkpoints are the ones the paper's trap probe used; they are loaded from the local
cache with network access disabled. A passage is 'title. text'. Every ranker returns a complete
ordering of the pool; budgets are applied later, identically for every ranker.

  <venv>/python harness/package2/rank_local.py ITEMS.jsonl OUT.jsonl
"""
import io
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
ND = ROOT / "natural_data"
TOK = re.compile(r"[a-z0-9]+")
MMR_LAMBDA = 0.5


def toks(s):
    return TOK.findall(s.lower())


def passage(p):
    return "%s. %s" % (p["title"], p["text"])


def idf_table(dataset):
    """Document frequencies over every paragraph of the dataset (the shared IDF of BM25)."""
    df, n = Counter(), 0
    src = ND / ("hotpot_dev_distractor.jsonl" if dataset == "hotpotqa" else "musique_ans_v1.0_dev.jsonl")
    for line in open(src, encoding="utf-8"):
        r = json.loads(line)
        paras = r["paragraphs"]
        for p in paras:
            text = passage(p) if "text" in p else "%s. %s" % (p["title"], p["paragraph_text"])
            df.update(set(toks(text)))
            n += 1
    return {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}, n


def bm25_scores(query, docs, idf, k1=1.5, b=0.75):
    dt = [Counter(toks(d)) for d in docs]
    lens = [sum(c.values()) for c in dt]
    avg = sum(lens) / max(1, len(lens))
    q = toks(query)
    out = []
    for c, L in zip(dt, lens):
        s = 0.0
        for t in q:
            f = c.get(t, 0)
            if f:
                s += idf.get(t, 0.0) * f * (k1 + 1) / (f + k1 * (1 - b + b * L / avg))
        out.append(s)
    return out


def order_by(scores):
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


def mmr_order(q_emb, d_emb, lam=MMR_LAMBDA):
    import numpy as np
    rel = (d_emb @ q_emb).tolist()
    sim = (d_emb @ d_emb.T)
    chosen, left = [], list(range(len(rel)))
    while left:
        def score(i):
            red = max((float(sim[i, j]) for j in chosen), default=0.0)
            return lam * rel[i] - (1 - lam) * red
        best = max(left, key=lambda i: (score(i), -i))
        chosen.append(best)
        left.remove(best)
    return chosen


def main(items_path, out_path):
    from sentence_transformers import CrossEncoder, SentenceTransformer
    items = [json.loads(l) for l in open(items_path, encoding="utf-8")]
    bge = SentenceTransformer("BAAI/bge-small-en-v1.5")
    e5 = SentenceTransformer("intfloat/e5-small-v2")
    ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    idfs = {}
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        for it in items:
            ds = it["dataset"]
            if ds not in idfs:
                idfs[ds] = idf_table(ds)[0]
            docs = [passage(p) for p in it["paragraphs"]]
            q = it["question"]
            res = {}
            sc = bm25_scores(q, docs, idfs[ds])
            res["bm25"] = (order_by(sc), sc)
            qb = bge.encode(["Represent this sentence for searching relevant passages: " + q], normalize_embeddings=True)[0]
            db = bge.encode(docs, normalize_embeddings=True)
            sc = (db @ qb).tolist()
            res["bge"] = (order_by(sc), sc)
            res["mmr"] = (mmr_order(qb, db), None)
            qe = e5.encode(["query: " + q], normalize_embeddings=True)[0]
            de = e5.encode(["passage: " + d for d in docs], normalize_embeddings=True)
            sc = (de @ qe).tolist()
            res["e5"] = (order_by(sc), sc)
            sc = [float(x) for x in ce.predict([(q, d) for d in docs])]
            res["minilm"] = (order_by(sc), sc)
            for name, (order, scores) in res.items():
                fh.write(json.dumps({"id": it["id"], "dataset": ds, "role": it["role"], "ranker": name,
                                     "order": order, "scores": scores}) + "\n")
    print("ranked %d items with 5 local rankers -> %s" % (len(items), out_path))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
