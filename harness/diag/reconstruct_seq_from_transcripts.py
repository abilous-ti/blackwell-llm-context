"""Reconstruct a prevalence_seq run whose driver crashed AFTER every draw was paid for, from the
per-call Claude CLI session transcripts (~/.claude/projects/<cwd-slug>/<session>.jsonl).

Why this is measured data and not re-labelling: in the original run every scored draw was
    claude -p reply text  ->  measure_blackwell._extract_code  ->  measure_blackwell.verify_in
(a deterministic verifier). The transcripts hold that exact reply text; this tool re-runs the same
extraction and the same verifier. The only inferred quantity, disclosed in the output, is WHICH
sessions the driver scored. A session was scored iff the CLI returned a non-error, non-empty result
within the driver's subprocess timeout and the reply used no tools (single-shot, max-turns 1).
Everything else -- usage-limit / connection errors (synthetic assistant messages), answers that
arrived after the timeout, tool-using replies the CLI aborted and the driver retried, manual
diagnostic calls made while the run was in flight -- was never seen by the driver's scorer.
Checksums: the run log's per-round 'verified pairs' counts and its final tallies must be reproduced
exactly; the reconstruction is accepted only if they are.

Partial runs (driver killed mid-round): pass --rounds-done R (from the log) and --ckpt-out FILE; the
checkpoint holds every scored draw so far (including the partial round) and prevalence_seq --resume
continues the run with the same rule. Driver-level calls = one temp dir per run_one = one project dir,
so calls are counted exactly from the transcripts; spend is estimated from token usage.
"""
import argparse, collections, datetime, glob, gzip, json, os, shutil, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import prevalence_seq as ps
import measure_blackwell as mb
REPO = HERE.parent.parent
TAIL = (" Return ONLY the raw Python file content, no markdown fences, no prose, "
        "and do NOT use any tools or write any files.")
USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
PRICE_PER_M = {"input_tokens": 1.00, "output_tokens": 5.00,                 # Haiku 4.5 list prices,
               "cache_creation_input_tokens": 1.25, "cache_read_input_tokens": 0.10}   # USD per 1M tokens


def short(dirname):
    """Project-dir slug -> the temp-dir id only (no user/machine path in anything that is committed)."""
    return dirname.split("Temp-")[-1]


def _ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)


def parse_session(path, dirname, nfiles):
    t0 = None; user = None; real = []; synth = []; tool_use = False
    usage = {k: 0 for k in USAGE_KEYS}; seen = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                continue
            typ = o.get("type")
            if o.get("timestamp") and t0 is None:
                t0 = _ts(o["timestamp"])
            if typ == "user":
                c = (o.get("message") or {}).get("content")
                if isinstance(c, str) and user is None:
                    user = c
                elif isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                    tool_use = True
            elif typ == "assistant":
                m = o.get("message") or {}
                blocks = m.get("content") or []
                if any(isinstance(b, dict) and b.get("type") == "tool_use" for b in blocks):
                    tool_use = True
                txt = "".join((b.get("text") or "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
                is_real = (m.get("model") or "").startswith("claude")
                (real if is_real else synth).append((_ts(o["timestamp"]), txt))
                if is_real and m.get("id") not in seen:          # one usage record per message, not per content line
                    seen.add(m.get("id")); u = m.get("usage") or {}
                    for k in USAGE_KEYS:
                        usage[k] += int(u.get(k) or 0)
    t_real = max((t for t, _ in real), default=None)
    return {"dir": dirname, "file": os.path.basename(path), "nfiles": nfiles, "t0": t0, "user": user,
            "text": "".join(t for _, t in real), "n_real": len(real), "n_synth": len(synth),
            "synth_text": (synth[0][1][:80] if synth else ""), "tool_use": tool_use, "usage": usage,
            "dur": (t_real - t0).total_seconds() if (t_real and t0) else None}


def est_cost(sessions):
    return sum(s["usage"][k] * PRICE_PER_M[k] / 1e6 for s in sessions for k in USAGE_KEYS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcripts", required=True, help="directory of copied project dirs, or a .jsonl(.gz) extract")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--nmax", type=int, default=24)
    ap.add_argument("--round", type=int, default=4)
    ap.add_argument("--futility", type=int, default=8)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--timeout", type=float, default=200.0, help="driver subprocess timeout (s)")
    ap.add_argument("--exclude", default="", help="comma-separated session dir names to drop (manual diagnostics)")
    ap.add_argument("--rounds-done", type=int, default=0, help="rounds the driver completed per its log; 0 = the whole run")
    ap.add_argument("--calls-from-log", type=int, default=0, help="override the dir count with the log's call count")
    ap.add_argument("--spend-from-log", type=float, default=0.0, help="CLI-reported spend from the log (else estimated from tokens)")
    ap.add_argument("--redrawn-from-log", type=int, default=0)
    ap.add_argument("--expect-rounds", default="", help="checksum: per-round verified-pair counts from the log, e.g. 0,0,1,3,3,4")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--classify-only", action="store_true")
    ap.add_argument("--extract-out", default="", help="write the redacted session extract (.jsonl or .jsonl.gz)")
    ap.add_argument("--ckpt-out", default="", help="write a prevalence_seq --resume checkpoint (partial runs)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    corpus = ps.load_corpus(a.corpus); TASKS = corpus.TASKS
    for t in TASKS:
        t.setdefault("fam", "prev")
    docs = ps.natural_chunks(corpus)
    topk = {t["id"]: ps.bm25_topk(t["prompt"], docs, k=a.topk) for t in TASKS}
    pool = sorted({d for ids in topk.values() for d in ids})
    by_task = [t["id"] for t in TASKS]
    tmap = {t["id"]: t for t in TASKS}
    ARMS = {"none": None, **{d["id"]: d["text"] for d in docs if d["id"] in pool}}
    expected = {}
    for arm, ctx in ARMS.items():
        for t in TASKS:
            expected[" ".join(((((ctx + "\n\n") if ctx else "") + t["prompt"]) + TAIL).split())] = (arm, t["id"])

    excl = {s.strip() for s in a.exclude.split(",") if s.strip()}
    sessions = []
    if a.transcripts.endswith((".jsonl", ".jsonl.gz")):
        # the committed, redacted extract (written by --extract-out): reply text + cell + timing + usage only
        opener = gzip.open if a.transcripts.endswith(".gz") else open
        with opener(a.transcripts, "rt", encoding="utf-8") as fh:
            sessions = [json.loads(l) for l in fh if l.strip()]
        for s in sessions:
            s["t0"] = datetime.datetime.fromisoformat(s["t0"]) if s["t0"] else None
            s["cell"] = tuple(s["cell"]) if s["cell"] else None
            s["user"] = None
            s.setdefault("usage", {k: 0 for k in USAGE_KEYS})
    else:
        for d in sorted(glob.glob(os.path.join(a.transcripts, "*"))):
            if not os.path.isdir(d):
                continue
            files = sorted(glob.glob(os.path.join(d, "*.jsonl")), key=os.path.getmtime)
            for f in files:
                sessions.append(parse_session(f, os.path.basename(d), len(files)))
    sessions.sort(key=lambda s: s["t0"] or datetime.datetime.min)

    # ---- classification -------------------------------------------------------------------------
    for s in sessions:
        s["cell"] = expected.get(s["user"]) if s["user"] else s.get("cell")
        if s["cell"] is None:
            s["status"] = "foreign"                              # another corpus / another run
        elif s["dir"] in excl:
            s["status"] = "excluded-manual"
        elif not s["text"].strip():
            s["status"] = "error"                                # synthetic: usage limit / no connection
        elif s["dur"] is None or s["dur"] >= a.timeout - 5:
            s["status"] = "timeout"                              # reply landed after the driver gave up
        elif s["tool_use"]:
            later = [x for x in sessions if x["dir"] == s["dir"] and x["t0"] > s["t0"]]
            s["status"] = "tool-use-retried" if later else "tool-use-alone"
        else:
            s["status"] = "scored"
    st = collections.Counter(s["status"] for s in sessions)
    run_sessions = [s for s in sessions if s["status"] not in ("foreign", "excluded-manual")]
    n_dirs = len({s["dir"] for s in run_sessions})               # one temp dir per driver-level run_one call
    cost_est = est_cost(run_sessions)
    print("sessions", len(sessions), dict(st), f"| driver calls (dirs) {n_dirs} | est. spend from tokens ${cost_est:.2f}")
    print("synthetic kinds:", collections.Counter(s["synth_text"][:60] for s in sessions if s["status"] == "error").most_common(5))
    border = [s for s in sessions if s["dur"] and a.timeout - 30 <= s["dur"] <= a.timeout + 30]
    print("borderline durations (timeout +-30 s):", [(s["cell"], round(s["dur"])) for s in border])
    for s in sessions:
        if s["status"].startswith("tool-use"):
            print(f"  tool-use  {s['status']:<17} {s['cell'][0].split('.')[-1]}|{s['cell'][1]:<10} {s['t0']:%d %H:%M:%S} dir={short(s['dir'])} nfiles={s['nfiles']} text[:70]={s['text'][:70]!r}")

    # ---- per-cell scored sessions and the count constraint --------------------------------------
    scored = [s for s in sessions if s["status"] == "scored"]
    per = collections.defaultdict(list)
    for s in scored:
        per[s["cell"]].append(s)
    problems = []
    for cell in sorted(per):
        n = len(per[cell])
        if n > a.nmax:
            problems.append(cell)
            print(f"  EXTRA  {cell[0]}|{cell[1]}: {n} scored sessions > nmax={a.nmax}:")
            for s in per[cell]:
                end = s["t0"] + datetime.timedelta(seconds=s["dur"])
                conc = sum(1 for x in sessions if x is not s and x["status"] in ("scored", "timeout", "error") and x["t0"]
                           and x["t0"] <= end and x["t0"] + datetime.timedelta(seconds=x["dur"] or 0) >= s["t0"])
                print(f"           {s['t0']:%d %H:%M:%S} dur {s['dur']:6.1f}s  concurrent-with {conc}  dir={short(s['dir'])}")
    if a.extract_out:
        # redacted provenance extract for the repository: no cwd, no environment attachments, no prompt
        # text (it is rebuilt from the corpus), only what the reconstruction consumes
        opener = gzip.open if a.extract_out.endswith(".gz") else open
        with opener(a.extract_out, "wt", encoding="utf-8") as fh:
            for s in sessions:
                fh.write(json.dumps({"dir": short(s["dir"]), "file": s["file"], "nfiles": s["nfiles"],
                                     "t0": s["t0"].isoformat() if s["t0"] else None, "dur": s["dur"],
                                     "cell": list(s["cell"]) if s["cell"] else None, "status": s["status"],
                                     "n_real": s["n_real"], "n_synth": s["n_synth"], "synth_text": s["synth_text"],
                                     "tool_use": s["tool_use"], "usage": s["usage"], "text": s["text"]}) + "\n")
        print("extract written:", a.extract_out, len(sessions), "sessions")
    if a.classify_only:
        print("classify-only: stop here.", "PROBLEM CELLS:" if problems else "no count problems", [f"{c[0]}|{c[1]}" for c in problems])
        return

    # ---- re-verification (same extraction, same verifier) ---------------------------------------
    def verify(s):
        wd = Path(tempfile.mkdtemp(prefix="rc_"))
        try:
            (wd / "solution.py").write_text(mb._extract_code(s["text"]), encoding="utf-8")
            return 1 if mb.verify_in(wd, tmap[s["cell"][1]]["verify"]) else 0
        finally:
            shutil.rmtree(wd, ignore_errors=True)
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for s, v in zip(scored, ex.map(verify, scored)):
            s["pass"] = v
    print(f"re-verified {len(scored)} scored sessions in {time.time() - t_start:.0f}s")

    # ---- none block -> leaky / clean / alpha (as the driver) ------------------------------------
    none_p = {t: sum(s["pass"] for s in per[("none", t)]) / a.nmax for t in by_task}
    leaky = [t for t in by_task if none_p[t] >= 0.5]
    clean = [t for t in by_task if t not in leaky]
    alpha = ps.ETA / (2 * len(clean)); a1 = a2 = alpha / 2
    print("none-baseline:", {t: f"{v:.0%}" for t, v in none_p.items()}, "| leaky:", leaky, f"| alpha={alpha:.4f}")
    for t in by_task:
        if len(per[("none", t)]) != a.nmax:
            print(f"  WARNING none|{t}: {len(per[('none', t)])} scored sessions (expected {a.nmax})")

    # ---- round boundaries: round r+1 opens with the earliest (r*round+1)-th draw of any cell ------
    cand_cells = [(x, t) for x in pool for t in clean]
    for cell in cand_cells:
        per[cell].sort(key=lambda s: s["t0"])
    R_total = a.nmax // a.round
    R_done = a.rounds_done or R_total
    starts = []
    for r in range(R_total):
        have = [per[c][a.round * r]["t0"] for c in cand_cells if len(per[c]) > a.round * r]
        if not have:
            break
        starts.append(min(have))
    for cell in cand_cells:
        for s in per[cell]:
            s["round"] = sum(1 for b in starts if b <= s["t0"])                       # 1-based
    for cell in cand_cells:
        cnt = collections.Counter(s["round"] for s in per[cell])
        if any(cnt[r] > a.round for r in cnt):
            print(f"  WARNING round assignment overflow {cell}: {dict(cnt)}")
    draws = {cell: [s["pass"] for s in per[cell]] for cell in cand_cells}
    draws.update({("none", t): [s["pass"] for s in per[("none", t)]] for t in by_task})
    errs = {k: [0] * len(v) for k, v in draws.items()}

    # ---- replay the driver's rule on the round-cumulative counts --------------------------------
    pairs = [(pool[i], pool[j]) for i in range(len(pool)) for j in range(i + 1, len(pool))]
    done = {}; active = set(cand_cells); stop_n = {}; n_drawn = 0; per_round_verified = []
    for r in range(1, R_done + 1):
        n_drawn += a.round
        cum = {c: [s["pass"] for s in per[c] if s["round"] <= r] for c in cand_cells}
        iv = {c: ps.av_interval(sum(cum[c]), len(cum[c]), a1) for c in cand_cells}
        for pr in pairs:
            if pr in done:
                continue
            s_, lab, lba = ps.pair_status(iv, pr[0], pr[1], clean)
            if s_ == "INCOMPARABLE":
                done[pr] = ("INCOMPARABLE", lab, lba, n_drawn)
        tot = {x: sum(sum(cum[(x, t)]) for t in clean) for x in pool}
        for cell in sorted(active):
            x, t = cell
            mine = [pr for pr in pairs if x in pr]
            open_partners = [pr[0] if pr[1] == x else pr[1] for pr in mine if pr not in done]
            hopeless = n_drawn >= a.futility and tot[x] == 0 and all(tot[p] == 0 for p in open_partners)
            if all(pr in done for pr in mine) or hopeless:
                active.discard(cell); stop_n[cell] = n_drawn
        nv = sum(1 for v in done.values() if v[0] == "INCOMPARABLE"); per_round_verified.append(nv)
        print(f"  round n={n_drawn:<3} verified pairs {nv:>2}/{len(pairs)}  active cells {len(active):>3}"
              f"  scored draws so far {sum(len(cum[c]) for c in cand_cells)}")
    if a.expect_rounds:
        exp = [int(v) for v in a.expect_rounds.split(",")]
        print("CHECKSUM per-round verified pairs:", per_round_verified, "expected", exp, "->", "MATCH" if exp == per_round_verified else "MISMATCH")
    stopped = dict(stop_n)                                       # cells the rule actually stopped
    calls = a.calls_from_log or n_dirs
    spend = a.spend_from_log or round(cost_est, 2)
    provenance = {"from": os.path.relpath(a.transcripts, REPO), "tool": "harness/diag/reconstruct_seq_from_transcripts.py",
                  "when": time.strftime("%Y-%m-%d %H:%M:%S"), "session_status": dict(st), "excluded_manual": sorted(excl),
                  "scoring_rule": f"scored iff real (non-synthetic) reply, no tool use, reply within the {a.timeout:.0f}s driver timeout",
                  "per_round_verified": per_round_verified, "expected_from_log": a.expect_rounds, "rounds_done": R_done,
                  "calls": "one project dir per driver-level run_one call" + (" (overridden by the log)" if a.calls_from_log else ""),
                  "calls_from_dirs": n_dirs, "spend_est_from_tokens_usd": round(cost_est, 2),
                  "spend": "CLI-reported total from the log" if a.spend_from_log else "estimated from token usage at Haiku 4.5 list prices",
                  "draw_order": "time order within a round (the driver's within-round job order is not recoverable; only round-cumulative counts enter the rule)",
                  "session_dirs": {f"{x}|{t}": [short(s["dir"]) for s in per[(x, t)]] for (x, t) in draws}}
    if a.ckpt_out:
        partial = sum(1 for c in cand_cells for s in per[c] if s["round"] > R_done)
        ck = {"corpus": a.corpus, "model": a.model, "nmax": a.nmax, "n_drawn": R_done * a.round,
              "counts": {f"{x}|{t}": [sum(v), len(v)] for (x, t), v in draws.items()},
              "draws": {f"{x}|{t}": v for (x, t), v in draws.items()},
              "errs": {f"{x}|{t}": v for (x, t), v in errs.items()},
              "done": {f"{pr[0]}|{pr[1]}": list(v) for pr, v in done.items()},
              "stop_n": {f"{x}|{t}": n for (x, t), n in stopped.items()},
              "calls": calls, "total_cost_usd": spend, "outage_redrawn": {}, "outage_unscored": {},
              "written": time.strftime("%Y-%m-%d %H:%M:%S"),
              "reconstructed": {**provenance, "partial_round_draws_kept": partial,
                                "note": "draws beyond n_drawn belong to the interrupted round; prevalence_seq --resume tops every active cell up to the round boundary before the next check"}}
        (REPO / a.ckpt_out).write_text(json.dumps(ps._strkeys(ck), indent=1), encoding="utf-8")
        print(f"checkpoint written: {a.ckpt_out}  n_drawn={R_done * a.round}  scored draws={sum(len(v) for v in draws.values())}  partial-round draws kept={partial}")
    if R_done < R_total:
        print(f"partial run ({R_done}/{R_total} rounds): no stage-2 verdicts; resume the driver from the checkpoint.")
        return
    for cell in active:
        stop_n[cell] = n_drawn

    # ---- stage 2: fixed-n CP at alpha/2 on the final counts (complete runs only) ----------------
    ivf = {c: ps.cp_interval(sum(draws[c]), len(draws[c]), a2) for c in cand_cells}
    rows = []
    for pr in pairs:
        if pr in done:
            s_, lab, lba, nstop = done[pr]
        else:
            s_, lab, lba = ps.pair_status(ivf, pr[0], pr[1], clean); nstop = a.nmax
            s_ = s_ if s_ == "INCOMPARABLE" else "unresolved"
        sa, sb = lab > 0, lba > 0
        pat = "incomparable" if (sa and sb) else ("one-way evidence" if (sa or sb) else "no evidence")
        co = any(pr[0] in ids and pr[1] in ids for ids in topk.values())
        rows.append({"pair": list(pr), "verdict": s_, "pattern": pat, "L_AB": round(lab, 3), "L_BA": round(lba, 3),
                     "co_retrieved": co, "n_at_verdict": nstop})
    tally = collections.Counter(r["verdict"] for r in rows); pat_all = collections.Counter(r["pattern"] for r in rows)
    pat_co = collections.Counter(r["pattern"] for r in rows if r["co_retrieved"])
    fixed_calls = (len(pool) + 1) * len(by_task) * a.nmax
    scored_draws = sum(len(v) for v in draws.values())
    residual = {f"{x}|{t}": a.nmax - len(draws[(x, t)]) for (x, t) in cand_cells if len(draws[(x, t)]) < a.nmax}
    print(f"verdicts: {dict(tally)}  | patterns ALL {dict(pat_all)}  CO-RETRIEVED {dict(pat_co)}")
    print(f"scored draws: {scored_draws} vs fixed-n {fixed_calls} -> {fixed_calls / scored_draws:.2f}x;  driver calls {calls};  unscored residual {sum(residual.values())}")
    out = {"corpus": a.corpus, "sequential": True, "mock": False, "model": a.model, "eta": ps.ETA,
           "nmax": a.nmax, "round": a.round, "futility": a.futility, "topk": topk, "pool": pool,
           "none_pass": none_p, "leaky_tasks": leaky, "clean_tasks": clean,
           "counts": {f"{x}|{t}": [sum(v), len(v)] for (x, t), v in draws.items()},
           "draws": {f"{x}|{t}": v for (x, t), v in draws.items()},
           "errs": {f"{x}|{t}": v for (x, t), v in errs.items()},
           "stop_n": {f"{x}|{t}": n for (x, t), n in stop_n.items()},
           "pairs": rows, "tally": dict(tally), "pattern_all": dict(pat_all), "pattern_co": dict(pat_co),
           "calls": calls, "fixed_calls": fixed_calls, "scored_draws": scored_draws,
           "total_cost_usd": spend,
           "outage_redrawn": a.redrawn_from_log, "outage_unscored": residual,
           "reconstructed": {**provenance,
                             "why": "driver crashed at the final json.dumps (tuple keys) after all draws completed; counts rebuilt from the per-call CLI transcripts with the same _extract_code + verify_in"}}
    if a.out:
        (REPO / a.out).write_text(json.dumps(ps._strkeys(out), indent=1), encoding="utf-8")
        print("wrote", REPO / a.out)


if __name__ == "__main__":
    main()
