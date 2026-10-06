r"""Leak check for the text-free natural-data exports (run after export_qa_textfree.py).

Scans every file in results/package2/confirm_qa_textfree/ and results/natural_pilot_textfree/ (and
the scripts that build and check them):

 (a) every JSON string, keys and values at any depth, longer than 40 characters must be a hex digest,
     an identifier (question, request, response, pilot item or schedule id, file path, analysis
     cell key), a model id, an ISO timestamp or an enum; shorter strings are classified too and any
     that fit no class are listed for reading; every line of the confirmation lists must be a
     question id;
 (b) no file may share a substring of 30 or more characters with any question, answer, paragraph
     title or text, Stage 1/2 source, annotation or model reply in the raw records (natural_data/,
     which stays local), compared exactly and again after lowercasing and collapsing whitespace.
     JSON files are also checked as their decoded strings, so escaped text cannot hide.

Method for (b): every export text is indexed by its 15-character grams at positions that are
multiples of 15. A common substring of length >= 30 always contains one such gram, so scanning every
position of every raw text against the index and extending each candidate in both directions finds
every common substring of length >= 30; nothing is sampled.

  python harness/package2/check_textfree_leaks.py          (needs the local natural_data/)
Exit status 1 on any hit.
"""
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
ND = ROOT / "natural_data"
EXPORTS = [ROOT / "results" / "package2" / "confirm_qa_textfree", ROOT / "results" / "natural_pilot_textfree"]
SCRIPTS = [ROOT / "harness" / "package2" / f for f in
           ("export_qa_textfree.py", "check_textfree_leaks.py", "verify_qa_textfree.py")]
MIN_LEN, GRAM, MAX_FIELD = 30, 15, 40

# ---- (a) string classes -----------------------------------------------------------------------
MODEL = r"(?:Haiku-4\.5|GPT-5\.5|DeepSeek-V4-Pro)"
HOTPOT = r"[0-9a-f]{24}"
MUSIQUE = r"[2-4]hop[1-3]?__\d+(?:_\d+)+"
QID = r"(?:%s|%s)" % (HOTPOT, MUSIQUE)
COND = r"(?:none|full|bm25|mmr|bge|e5|minilm|rankgpt|gold|gold\+dist|dist\+gold)"
PILOT_ITEM = r"(?:T\d{2}-(?:table|text|table-text)|H\d{2}-(?:sq[12]|orig))"
CLASSES = [
    ("hex digest", r"[0-9a-f]{64}"),
    ("question id", QID),
    ("TAT-QA uid", r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
    ("ISO timestamp", r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:\+00:00|Z)"),
    ("model id", r"%s|claude-haiku-4-5(?:-\d{8})?|gpt-5\.5" % MODEL),
    ("request id", r"ans\|%s\|%s\|%s|rank\|%s\|%s\|o[01]|over\|%s\|%s\|(?:5|10|20)\|o[01]"
     % (MODEL, QID, COND, MODEL, QID, MODEL, QID)),
    ("response id", r"msg_[A-Za-z0-9]{20,32}|resp_[0-9a-f]{40,64}|[0-9a-f]{32}"),
    ("pilot item id", PILOT_ITEM + r"|[TH]\d{2}"),
    ("pilot schedule id", r"%s\|%s\|(?:none|A|B|AB|BA)\|[0-2]" % (MODEL, PILOT_ITEM)),
    ("analysis cell key", r"(?:hotpotqa|musique)\|(?:bm25|mmr|bge|e5|minilm|rankgpt)"
     r"|(?:hotpot_rank|musique_rank|hotpot_aug)\|%s\|(?:%s|rankgpt-(?:bm25|mmr|bge|e5|minilm))"
     r"|%s\|(?:gold\+dist|dist\+gold) - gold\|(?:em|f1)|%s\|(?:5|10|20)" % (MODEL, COND, MODEL, MODEL)),
    ("file path", r"(?:natural_data|harness|results)/[A-Za-z0-9_./-]+|[A-Za-z0-9_.-]+\.(?:txt|json|jsonl|parquet|py|md)"),
    ("content-filter flag", r"(?:prompt|completion):[a-z_]+"),
    ("content-filter label", r"MultiSeverity_[A-Za-z]+Score"),
    ("MuSiQue hop type", r"[2-4]hop[1-3]?"),
    ("empty label", r""),                                     # e.g. TAT-QA's scale for unscaled answers
    ("identifier or enum", r"[A-Za-z][A-Za-z0-9_+.\-]*"),    # snake_case keys, labels, enums (no spaces)
]
CLASSES = [(name, re.compile(r"(?:%s)\Z" % pat)) for name, pat in CLASSES]


def classify(s):
    for name, rx in CLASSES:
        if rx.match(s) and (name != "identifier or enum" or len(s) <= MAX_FIELD):
            return name
    return None


def json_strings(x, path="$"):
    """(path, string) for every key and string value."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield path + ".<key>", k
            yield from json_strings(v, path + "." + k)
    elif isinstance(x, list):
        for v in x:
            yield from json_strings(v, path + "[]")
    elif isinstance(x, str):
        yield path, x


def load_json_any(p):
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".jsonl":
        return [json.loads(l) for l in text.split("\n") if l.strip()]
    return [json.loads(text)]


def check_fields(files):
    """(a): strings over MAX_FIELD outside the specific classes; plus, per JSON path, the values of
    the generic identifier/enum class and of anything unclassified, so they can be read."""
    long_bad, values, census = [], defaultdict(Counter), Counter()
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix in (".json", ".jsonl"):
            for obj in load_json_any(p):
                for path, s in json_strings(obj):
                    c = classify(s)
                    census[c or "UNCLASSIFIED"] += 1
                    if c is None and len(s) > MAX_FIELD:
                        long_bad.append((rel, path, len(s)))
                    elif c in (None, "identifier or enum"):
                        cell = re.sub(r"\.[^.<]*\|[^.<]*", ".<cell>", path)
                        values[(rel, cell, c or "UNCLASSIFIED")][s] += 1
        elif p.name.startswith("confirmation_") and p.suffix == ".txt":
            for i, line in enumerate(p.read_text(encoding="utf-8").split("\n")):
                if line and classify(line) != "question id":
                    long_bad.append((rel, "line %d" % (i + 1), len(line)))
    return long_bad, values, census


# ---- (b) shared substrings with the raw texts --------------------------------------------------
SKIP_KEYS = {"id", "uid", "doc_uid", "item", "model", "requested_model", "returned_model", "response_id",
             "schedule_id", "prompt_sha256", "start_utc", "end_utc", "utc", "created", "created_at",
             "completed_at", "object", "type", "role", "status", "window"}


def raw_strings(x, key=None):
    """Every string in a raw record except identifiers and timestamps (which the export carries)."""
    if isinstance(x, dict):
        for k, v in x.items():
            if k in SKIP_KEYS or k.endswith("_id"):
                continue
            yield from raw_strings(v, k)
    elif isinstance(x, list):
        for v in x:
            yield from raw_strings(v, key)
    elif isinstance(x, str) and len(x) >= MIN_LEN and x != "<raw_text>":
        yield x


def raw_texts():
    """(label, text) for every text the export must not share: benchmark items, Stage 1/2 sources
    and annotations, and every reply, response envelope and provider error body."""
    p2 = ND / "package2"
    for f in ("items_confirm.jsonl", "items_pilot.jsonl"):
        for line in open(p2 / f, encoding="utf-8"):
            it = json.loads(line)
            yield f, it["question"]
            for a in it["answers"]:
                yield f, str(a)
            for p in it["paragraphs"]:
                yield f, p["title"]
                yield f, p["text"]
    for d in ("confirm_qa", "pilot_qa"):
        path = p2 / d / "records.jsonl"
        if not path.exists():
            continue
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r.get("type") != "receipt":
                continue
            yield d, r.get("raw_text") or ""
            for s in raw_strings(r.get("response")):
                yield d + " envelope", s
            for a in r.get("attempts") or []:
                for s in (a.get("error"), a.get("error_body")):
                    if s:
                        yield d + " error", s
    for f in ("stage1/sample.json", "stage1/audit.json", "stage2/items.json", "stage2/scored.json"):
        for s in raw_strings(json.load(open(ND / f, encoding="utf-8"))):
            yield f, s
    for line in open(ND / "stage2" / "records" / "pilot.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r.get("type") == "receipt":
            yield "stage2 records", r.get("raw_text") or ""
            for s in raw_strings(r.get("response")):
                yield "stage2 envelope", s


def norm(s):
    return " ".join(s.lower().split())


def export_views(files):
    views = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8")
        views.append((rel, text))
        if p.suffix in (".json", ".jsonl"):    # decoded string values: escaped text cannot hide
            views.append((rel + " [decoded strings]", "\n".join(
                s for o in load_json_any(p) for path, s in json_strings(o) if not path.endswith("<key>"))))
    return views


def build_index(texts):
    """hash(gram) -> packed (view << 32 | position) for every gram at a multiple of GRAM. Hashes keep
    the index small; every candidate is compared character by character, so collisions cost time only."""
    idx = {}
    for vid, t in enumerate(texts):
        for p in range(0, len(t) - GRAM + 1, GRAM):
            h, code = hash(t[p:p + GRAM]), (vid << 32) | p
            old = idx.get(h)
            if old is None:
                idx[h] = code
            elif isinstance(old, list):
                old.append(code)
            else:
                idx[h] = [old, code]
    return idx


def scan(views, limit=20):
    """Every common substring of length >= MIN_LEN between a raw text and an export view, exact and
    normalized; the two variants run one after the other to keep memory low."""
    shown, n_hits, n_chars, n_texts = [], 0, 0, 0
    for name, f in (("exact", lambda s: s), ("normalized", norm)):
        texts = [f(t) for _, t in views]
        idx = build_index(texts)
        seen = set()
        for label, raw in raw_texts():
            if len(raw) < MIN_LEN:
                continue
            if name == "exact":
                n_texts += 1
                n_chars += len(raw)
            t = f(raw)
            for q in range(len(t) - GRAM + 1):
                c = idx.get(hash(t[q:q + GRAM]))
                if c is None:
                    continue
                g = t[q:q + GRAM]
                for code in (c if isinstance(c, list) else (c,)):
                    vid, p = code >> 32, code & 0xFFFFFFFF
                    e = texts[vid]
                    if e[p:p + GRAM] != g:
                        continue
                    back = 0
                    while q - back > 0 and p - back > 0 and t[q - back - 1] == e[p - back - 1]:
                        back += 1
                    fwd = GRAM
                    while q + fwd < len(t) and p + fwd < len(e) and t[q + fwd] == e[p + fwd]:
                        fwd += 1
                    if back + fwd >= MIN_LEN and (vid, p - back, back + fwd) not in seen:
                        seen.add((vid, p - back, back + fwd))
                        n_hits += 1
                        if len(shown) < limit:
                            shown.append((name, views[vid][0], label, back + fwd))
        del idx, texts
    return shown, n_hits, n_texts, n_chars


def main():
    files = sorted(p for d in EXPORTS for p in d.rglob("*") if p.is_file()) + [s for s in SCRIPTS if s.exists()]
    exports = [p for p in files if p.suffix != ".py"]
    print("files checked: %d (%d export files, %d scripts)" % (len(files), len(exports), len(files) - len(exports)))
    long_bad, values, census = check_fields(exports)
    print("\n(a) JSON strings by class: %s" % ", ".join("%s %d" % kv for kv in sorted(census.items(), key=str)))
    print("    strings over %d characters that are not a digest, id, model id, timestamp or enum: %d"
          % (MAX_FIELD, len(long_bad)))
    for r in long_bad[:20]:
        print("      %s %s (%d chars)" % r)
    unclassified = {k: v for k, v in values.items() if k[2] == "UNCLASSIFIED"}
    print("    short strings outside every class: %s" % (sum(sum(c.values()) for c in unclassified.values()) or "none"))
    print("    values of the generic identifier/enum class, per field (keys excluded):")
    for (rel, path, cls), c in sorted(values.items()):
        if path.endswith("<key>") and cls != "UNCLASSIFIED":
            continue
        shown = ", ".join("%s" % v for v, _ in sorted(c.items())[:14]) + (" ... (%d distinct)" % len(c) if len(c) > 14 else "")
        print("      %s%s %s: %s" % ("UNCLASSIFIED " if cls == "UNCLASSIFIED" else "", rel.split("/")[-2] + "/" + rel.split("/")[-1], path, shown))
    keys = sorted({s for (rel, path, cls), c in values.items() if path.endswith("<key>") for s in c})
    print("    JSON keys (generic class): %d distinct: %s" % (len(keys), ", ".join(keys)))
    views = export_views(files)
    shown, n_hits, n_texts, n_chars = scan(views)
    print("\n(b) raw texts compared: %d texts, %.1f million characters; export views indexed: %d"
          % (n_texts, n_chars / 1e6, len(views)))
    print("    shared substrings of %d or more characters (exact or normalized): %d" % (MIN_LEN, n_hits))
    for name, view, label, n in shown:
        print("      [%s] %s <-> %s, %d chars" % (name, view, label, n))
    ok = not long_bad and not n_hits
    print("\nLEAK CHECK: %s" % ("PASS (zero hits)" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
