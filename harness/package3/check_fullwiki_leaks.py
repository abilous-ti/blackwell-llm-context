r"""Leak check for the text-free package-3 export (run after export_fullwiki_textfree.py).

Scans every file in results/package3/confirm_fullwiki_textfree/, the analysis files beside it and
every file in harness/package3/ (the code and notes committed with the export). Where the authors'
freeze is present (results/package3/FREEZE_fullwiki.json, or FULLWIKI_FREEZE=<path>), it is reported
on its own: it lists every candidate title, which is why it is kept by the authors and not
committed, so its hits are counted but do not decide the result.

 (a) Every JSON string, keys and values at any depth, must belong to a named class: hex digest, Git
     revision, question id, request id, response id, model id, ISO timestamp, file path, dataset URL,
     analysis key, content-filter flag or label, a constant of analyze_fullwiki.py's verdict, a count
     (keys only), or a short identifier or enum (at most 40 characters, no spaces). A string outside
     every class fails the check.
 (b) No file may share a substring of 30 or more characters with any question, answer, title,
     paragraph, model reply, response envelope or provider error message in natural_data/package3
     (the confirmatory and smoke items and records, and the sample's candidate titles), compared
     exactly and again after lowercasing and collapsing whitespace; JSON files are also checked as
     their decoded strings. Envelopes and error bodies are read as package 2 reads envelopes: every
     string value except identifiers and timestamps (error_texts below says why). The scan is package
     2's (check_textfree_leaks.scan), which finds every common substring of 30 or more characters;
     nothing is sampled.
 (c) Every distinct short string (at most 40 characters) is listed by key, except the values of the
     structured classes (digests, revisions, question, request and response ids, timestamps): their
     patterns admit no words, so they are counted. Numeric fields are listed with their range, and
     the digit keys of count distributions by path. Then every string, key or value, is compared with
     the 310 gold answers (confirmatory and smoke). Every string equal to a gold answer after
     HotpotQA's answer normalization is listed with where it occurs; it fails the check unless it
     occurs only as a count key (a category of a count distribution, such as questions with 3
     candidates). A string containing a gold answer of four or more characters as a whole-token
     sequence is listed for reading. The export's text files (README, analysis report, summary) are
     searched the same way.

  python harness/package3/check_fullwiki_leaks.py          (needs the local natural_data/package3)
Exit status 1 on any failure.
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True          # never write bytecode next to package 2's modules
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "package2"))
import check_textfree_leaks as C2  # noqa: E402  (JSON walking, normalization, the substring scan)
import analyze_fullwiki as AF  # noqa: E402
import fullwiki_data as FD  # noqa: E402

Q = AF.Q
P3 = ROOT / "natural_data" / "package3"
RES3 = ROOT / "results" / "package3"
EXPORT = RES3 / "confirm_fullwiki_textfree"
FREEZE = Path(os.environ.get("FULLWIKI_FREEZE") or RES3 / "FREEZE_fullwiki.json")   # the authors' copy only
MIN_LEN, MAX_FIELD = C2.MIN_LEN, C2.MAX_FIELD     # 30 and 40, as in package 2
MIN_ANSWER = 4                                     # gold answers searched as token sequences

# ---- (a) string classes -----------------------------------------------------------------------
MODEL = r"(?:Haiku-4\.5|GPT-5\.5|DeepSeek-V4-Pro)"
QID = r"[0-9a-f]{24}"
COND = r"(?:none|full|bm25|mmr|bge|e5|minilm|rankgpt)"
LOCAL = r"(?:bm25|mmr|bge|e5|minilm)"
GROUP = r"(?:all|sufficient|complement)"
STATUS = r"(?:received|failed_http400|failed_other|interrupted|not_issued|not_requested_no_rankgpt_ranking)"
# The verdict's prose is the analysis code's own constants (READING, and the note verdict() writes).
_v = AF.verdict({"primary": {}, "secondary": {}, "worst_case": {}, "evidence_criterion": {"holds": False}})
VERDICT = sorted(set(AF.READING) | set(AF.READING.values()) | {_v["worst_case"]["note"]})
STRUCTURED = ("hex digest", "Git revision", "question id", "request id", "response id", "ISO timestamp")
CLASSES = [
    ("hex digest", r"[0-9a-f]{64}"),
    ("Git revision", r"[0-9a-f]{40}"),
    ("question id", QID),
    ("response id", r"msg_[A-Za-z0-9]{20,32}|resp_[0-9a-f]{40,64}|[0-9a-f]{32}"),
    ("ISO timestamp", r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:\+00:00|Z)"),
    ("request id", r"ans\|%s\|%s\|%s|rank\|Haiku-4\.5\|%s\|o[01]" % (MODEL, QID, COND, QID)),
    ("model id", r"%s|claude-haiku-4-5(?:-\d{8})?|gpt-5\.5|BAAI/bge-small-en-v1\.5|intfloat/e5-small-v2"
     r"|cross-encoder/ms-marco-MiniLM-L-6-v2" % MODEL),
    ("analysis key", r"%s\|%s\|%s|%s\|%s\|rankgpt-%s|%s\|rankgpt-%s|rankgpt-%s|%s\|%s|%s\|%s|o[01]\|%s"
     % (GROUP, MODEL, COND, GROUP, MODEL, LOCAL, MODEL, LOCAL, LOCAL, GROUP, COND, MODEL, COND, STATUS)),
    ("file path", r"(?:natural_data|harness|results)/[A-Za-z0-9_./-]+"
     r"|(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:txt|json|jsonl|parquet|py|md|safetensors)"),
    ("dataset URL", re.escape(FD.SRC_URL)),
    ("content-filter flag", r"(?:prompt|completion):[a-z_]+"),
    ("content-filter label", r"MultiSeverity_[A-Za-z]+Score"),
    ("verdict constant", "|".join(re.escape(v) for v in VERDICT)),
    ("identifier or enum", r"[A-Za-z][A-Za-z0-9_+.\-]*"),      # at most MAX_FIELD characters
]
KEY_CLASSES = [("count", r"\d+")]                               # digit strings only as keys
CLASSES = [(n, re.compile(r"(?:%s)\Z" % p)) for n, p in CLASSES]
KEY_CLASSES = [(n, re.compile(r"(?:%s)\Z" % p)) for n, p in KEY_CLASSES]
DATA_KEYS = ("analysis key", "file path", "model id", "count")   # keys that are data, not field names


def classify(s, key=False):
    for name, rx in (KEY_CLASSES if key else []) + CLASSES:
        if rx.match(s) and (name != "identifier or enum" or len(s) <= MAX_FIELD):
            return name
    return None


def walk(x, path=()):
    """(path, string, is_key) for every key and string value; numbers as (path, number, None).
    Keys that are data (cell keys, file paths, model names, counts) are generalized in the path."""
    if isinstance(x, dict):
        for k, v in x.items():
            c = classify(k, key=True)
            yield path, k, True
            yield from walk(v, path + ("<%s>" % c if c in DATA_KEYS else k,))
    elif isinstance(x, list):
        for v in x:
            yield from walk(v, path + ("[]",))
    elif isinstance(x, str):
        yield path, x, False
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield path, x, None


# ---- (b) the raw texts --------------------------------------------------------------------------
def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


HTTP_ERROR = re.compile(r"[A-Za-z]+Error: HTTP Error \d{3}: [A-Za-z ]+\Z")
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"(\s*:)?')
UNTERMINATED = re.compile(r'"((?:[^"\\]|\\.)*)\Z')


def unescape(lit):
    try:
        return json.loads('"%s"' % lit)
    except ValueError:                          # cut inside an escape sequence
        return lit


def error_texts(a):
    """The texts of one failed attempt. The body is a provider response and is read as package 2 reads
    response envelopes (check_textfree_leaks.raw_strings): every string value except identifiers
    and timestamps, which the export carries; keys and JSON punctuation are not text. Compared whole,
    a DeepSeek body matched the export's own JSON syntax around the model label (an identifier).
    The transport keeps at most 500 characters of a body, so a cut body is read literal by literal,
    the unterminated last one included. The exception string is compared too, except urllib's fixed
    form 'HTTPError: HTTP Error <code>: <reason>', which holds only the HTTP status line (status and
    error class are exported; the frozen run_fullwiki.py repeats that form in its mock replies)."""
    e = a.get("error")
    if e and not HTTP_ERROR.match(e):
        yield e
    body = a.get("error_body")
    if not body:
        return
    try:
        yield from C2.raw_strings(json.loads(body))
        return
    except ValueError:
        pass
    key, end = None, 0
    for m in LITERAL.finditer(body):
        end = m.end()
        if m.group(2):                          # a key
            key = m.group(1)
        elif not (key in C2.SKIP_KEYS or (key or "").endswith("_id")):
            yield unescape(m.group(1))
    m = UNTERMINATED.search(body, end)
    if m and not (key in C2.SKIP_KEYS or (key or "").endswith("_id")):
        yield unescape(m.group(1))


def raw_texts():
    """(label, text) for every text the export must not share: questions, answers, titles and
    paragraphs of the confirmatory and smoke items, the sample's candidate titles, and every reply,
    response envelope and provider error message in the confirmatory, smoke and mock records."""
    for f in ("items_confirm.jsonl", "items_smoke.jsonl"):
        for it in jl(P3 / f):
            yield f, it["question"]
            for a in it["answers"]:
                yield f, str(a)
            for t in it["supporting_titles"]:
                yield f, t
            for p in it["paragraphs"]:
                yield f, p["title"]
                yield f, p["text"]
    sample = json.load(open(P3 / "sample.json", encoding="utf-8"))
    for g in ("confirm", "smoke"):
        for x in sample[g]:
            for t in x["candidate_titles"]:
                yield "sample.json", t
    for d in ("confirm_fullwiki", "smoke_fullwiki", "mock_fullwiki"):
        path = P3 / d / "records.jsonl"
        if not path.exists():
            continue
        for r in jl(path):
            if r.get("type") != "receipt":
                continue
            yield d, r.get("raw_text") or ""
            for s in C2.raw_strings(r.get("response")):
                yield d + " envelope", s
            for a in r.get("attempts") or []:
                for s in error_texts(a):
                    yield d + " error", s


def gold_answers():
    return [(it["id"], a) for f in ("items_confirm.jsonl", "items_smoke.jsonl") for it in jl(P3 / f)
            for a in it["answers"]]


# ---- (c) answers ------------------------------------------------------------------------------
ARTICLES = {"a", "an", "the"}


def tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", str(s).lower()) if t not in ARTICLES]


def containing(golds):
    """A function returning (matched tokens, question id) for every gold answer (of MIN_ANSWER or
    more characters, yes/no excluded) that occurs in a string as a whole-token sequence. The matched
    tokens are a piece of the searched string, so printing them shows no text beyond the export."""
    first = defaultdict(list)
    for qid, a in golds:
        t = tokens(a)
        if t and len("".join(t)) >= MIN_ANSWER and Q.normalize_answer(a) not in ("yes", "no"):
            first[t[0]].append((tuple(t), qid))

    def find(s):
        ts, out = tokens(s), set()
        for i, t in enumerate(ts):
            for g, qid in first.get(t, ()):
                if tuple(ts[i:i + len(g)]) == g:
                    out.add((" ".join(g), qid))
        return out
    return find


def main():
    exports = sorted(p for p in EXPORT.rglob("*") if p.is_file())
    extra = [RES3 / "analysis_fullwiki.json", RES3 / "analysis_fullwiki.md"]
    harness = sorted(p for p in HERE.iterdir() if p.is_file())
    files = exports + extra + harness
    freeze = [FREEZE] if FREEZE.is_file() else []
    print("files checked: %d export files, %d analysis files beside the export, %d files in harness/package3; "
          "reported on its own: %s" % (len(exports), len(extra), len(harness),
                                       "the authors' freeze, %s" % freeze[0].as_posix() if freeze else "none (freeze not present)"))

    # (a) and the census for (c) ---------------------------------------------------------------------
    bad, census, values, numbers, keys = [], Counter(), defaultdict(Counter), defaultdict(list), defaultdict(set)
    count_keys = defaultdict(set)
    where = defaultdict(set)                     # every distinct string -> (file, path, is key, class)
    for p in exports:
        if p.suffix not in (".json", ".jsonl"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        for obj in C2.load_json_any(p):
            for path, s, is_key in walk(obj):
                if is_key is None:
                    numbers[(p.name, "/".join(path))].append(s)
                    continue
                c = classify(s, key=is_key)
                census[c or "UNCLASSIFIED"] += 1
                where[s].add((p.name, "/".join(path) or "$", is_key, c))
                if c is None:
                    bad.append((rel, "/".join(path) + (" <key>" if is_key else ""), len(s)))
                if is_key:
                    keys[p.name].add(s if c not in DATA_KEYS else "<%s>" % c)
                    if c == "count":
                        count_keys[(p.name, "/".join(path))].add(s)
                else:
                    values[(p.name, "/".join(path))][(c, s)] += 1
    print("\n(a) JSON strings by class: %s" % ", ".join("%s %d" % kv for kv in sorted(census.items())))
    print("    strings outside every class (keys or values, any length): %d" % len(bad))
    for r in bad[:20]:
        print("      %s %s (%d chars)" % r)

    # (c) every distinct short value by key -----------------------------------------------------------
    print("\n(c) string values by key (file / path): structured classes counted, every other distinct value listed")
    for (fname, path), cnt in sorted(values.items()):
        cls = Counter()
        for (c, s), n in cnt.items():
            cls[c] += n
        distinct = len(cnt)
        if set(cls) <= set(STRUCTURED):
            print("      %s %s: %d strings, %d distinct, all %s" % (fname, path or "$", sum(cls.values()), distinct,
                                                                  " / ".join(sorted(cls))))
        else:
            vals = ", ".join("%s (%d)" % (s, n) for (c, s), n in sorted(cnt.items(), key=lambda kv: kv[0][1]))
            print("      %s %s: %d distinct: %s" % (fname, path or "$", distinct, vals))
    print("    numeric fields (file / path: count, min, max):")
    for (fname, path), xs in sorted(numbers.items()):
        print("      %s %s: %d, %s to %s" % (fname, path or "$", len(xs), min(xs), max(xs)))
    for fname, ks in sorted(keys.items()):
        print("    keys of %s (%d distinct): %s" % (fname, len(ks), ", ".join(sorted(ks))))
    print("    count keys (digit strings, allowed only as keys of count distributions), by path:")
    for (fname, path), ks in sorted(count_keys.items()):
        print("      %s %s: %s" % (fname, path or "$", ", ".join(sorted(ks, key=int))))

    golds = gold_answers()
    normalized = {}
    for qid, a in golds:
        n = Q.normalize_answer(a)
        if n:
            normalized.setdefault(n, []).append(qid)
    equal = {s: occ for s, occ in where.items() if Q.normalize_answer(s) in normalized}
    # A count key names a category of a distribution of counts (for example, questions with 3
    # candidates), written by the code as str(int); every other string equal to an answer fails.
    failing = {s: occ for s, occ in equal.items() if any(not k or c != "count" for _, _, k, c in occ)}
    find = containing(golds)
    contain = {s: find(s) for s in where}
    contain = {s: v for s, v in contain.items() if v}
    text_hits = {}
    for p in exports:
        if p.suffix in (".md", ".txt"):
            hits = find(p.read_text(encoding="utf-8"))
            if hits:
                text_hits[p.name] = hits
    print("    gold answers compared: %d (%d distinct after normalization; %d of %d or more characters searched as "
          "token sequences)" % (len(golds), len(normalized), sum(1 for _, a in golds if len("".join(tokens(a))) >= MIN_ANSWER),
                                MIN_ANSWER))
    print("    JSON strings (keys and values) equal to a gold answer after normalization: %d; of these, values "
          "or keys other than count keys: %d" % (len(equal), len(failing)))
    for s, occ in sorted(equal.items()):
        print("      %r (answer of %s) occurs as %s" % (s, ", ".join(normalized[Q.normalize_answer(s)]), "; ".join(
            "%s in %s %s" % ("%s key" % c if k else "%s value" % c, f, path) for f, path, k, c in sorted(occ, key=str))))
    print("    JSON strings containing a gold answer as a token sequence: %d" % len(contain))
    for s, v in sorted(contain.items())[:30]:
        print("      %r: tokens %s" % (s, "; ".join("'%s' (answer of %s)" % m for m in sorted(v))))
    print("    text files containing a gold answer as a token sequence: %s"
          % ("; ".join("%s: %s" % (k, "; ".join("'%s' (answer of %s)" % m for m in sorted(v)))
                       for k, v in sorted(text_hits.items())) or "none"))

    # (b) shared substrings ------------------------------------------------------------------------
    views = C2.export_views(files)
    freeze_views = []
    for p in freeze:                             # as check_textfree_leaks.export_views, for a file anywhere
        freeze_views.append(("FREEZE " + p.name, p.read_text(encoding="utf-8")))
        freeze_views.append(("FREEZE " + p.name + " [decoded strings]", "\n".join(
            s for o in C2.load_json_any(p) for path, s in C2.json_strings(o) if not path.endswith("<key>"))))
    C2.raw_texts = raw_texts                    # C2.scan reads its raw texts through this module-level name
    shown, n_hits, n_texts, n_chars = C2.scan(views + freeze_views, limit=10 ** 9)
    mine = [h for h in shown if not h[1].startswith("FREEZE ")]
    theirs = [h for h in shown if h[1].startswith("FREEZE ")]
    print("\n(b) raw texts compared: %d texts of %d or more characters, %.1f million characters; views indexed: %d"
          % (n_texts, MIN_LEN, n_chars / 1e6, len(views)))
    print("    shared substrings of %d or more characters, export, analysis and harness files (exact or normalized): %d"
          % (MIN_LEN, len(mine)))
    for name, view, label, n in mine[:20]:
        print("      [%s] %s <-> %s, %d chars" % (name, view, label, n))
    by = Counter((h[0], h[2]) for h in theirs)
    if freeze:
        print("    INFO the authors' freeze (kept by the authors, not committed; it lists the candidate titles): %d shared "
              "substrings%s" % (len(theirs), (" (%s; longest %d chars)" % (
                  ", ".join("%s %s %d" % (k[0], k[1], v) for k, v in sorted(by.items())), max(h[3] for h in theirs)))
                                if theirs else ""))
    else:
        print("    INFO freeze not present; skipped (it is kept by the authors and not committed)")

    ok = not bad and not failing and not mine
    print("\nLEAK CHECK: %s" % ("PASS (zero hits in the export, the analysis files and harness/package3)" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
