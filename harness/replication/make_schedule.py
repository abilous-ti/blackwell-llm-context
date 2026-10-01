r"""Generate the complete randomized-block schedule before any response is collected.

For each window and model, every task contributes blocks_per_window blocks; each block holds one
request per condition of that task in a random order, and the blocks of the three tasks are
interleaved in a random order across the window. A model therefore meets every compared condition
throughout every window, and the conditions of one block are requested back to back.

The schedule depends only on design.json (including scheduler_seed, which is unrelated to any model
sampling seed; none is set). It is written with its SHA-256; freeze.py writes the frozen schedule and
records its hash in FREEZE.json, and run_replication.py refuses a schedule whose hash has changed.

Usage:  python harness/replication/make_schedule.py            (a draft preview; freeze.py writes the frozen one)
"""
import hashlib
import io
import json
import os
import random
import sys
from datetime import datetime, timezone

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "results", "replication")


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def build(design):
    rng = random.Random(design["scheduler_seed"])
    rows = []
    for w in design["windows"]:
        for m in design["models"]:
            blocks = [(t, k) for t in design["cells"] for k in range(design["blocks_per_window"])]
            rng.shuffle(blocks)
            seq = 0
            for bseq, (t, k) in enumerate(blocks):
                conds = list(design["cells"][t])
                rng.shuffle(conds)
                for pos, c in enumerate(conds):
                    rows.append({"schedule_id": "%s|%s|%s|%03d|%s" % (w["id"], m["label"], t, k, c),
                                 "window": w["id"], "model": m["label"], "task": t, "block": k,
                                 "block_seq": bseq, "position": pos, "condition": c,
                                 "seq_in_window": seq})
                    seq += 1
    return rows


def main(design_path=os.path.join(HERE, "design.json"), out_dir=OUT, suffix=None):
    design = json.load(open(design_path, encoding="utf-8"))
    frozen = design.get("status") == "frozen"
    tag = suffix or ("" if frozen else ".DRAFT")
    os.makedirs(out_dir, exist_ok=True)
    rows = build(design)
    sched = os.path.join(out_dir, "schedule%s.jsonl" % tag)
    with open(sched, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    manifest = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "design_status": design.get("status"), "scheduler_seed": design["scheduler_seed"],
                "design_sha256": sha256_file(design_path), "schedule_file": os.path.basename(sched),
                "schedule_sha256": sha256_file(sched), "n_requests": len(rows),
                "n_windows": len(design["windows"]), "n_models": len(design["models"]),
                "blocks_per_window": design["blocks_per_window"]}
    json.dump(manifest, open(os.path.join(out_dir, "schedule%s_manifest.json" % tag), "w",
                             encoding="utf-8"), indent=1)
    per = len(design["windows"]) * design["blocks_per_window"]
    print("%s schedule: %d requests (%d windows x %d models x %d conditions x %d blocks per window);"
          " n = %d per condition" % ("FROZEN" if frozen else "DRAFT", len(rows), len(design["windows"]),
                                      len(design["models"]), sum(len(v) for v in design["cells"].values()),
                                      design["blocks_per_window"], per))
    print("  %s  sha256 %s" % (os.path.relpath(sched, ROOT), manifest["schedule_sha256"][:16]))
    return sched, manifest


if __name__ == "__main__":
    main()
