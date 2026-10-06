r"""Declarative label tasks over the certified pair families (PROTOCOL_LABELS.md).

The decision is a convention label chosen from a finite menu, graded by comparing the chosen
number with the hidden state in this process; nothing the model writes is executed.

For each pair (inventory, audit) and each source X in {A, B} the X-label task asks which point
of X's declared family is in force. The menu lists every point of the family in the fixed order
of pairs.states(); the question and the menu do not depend on the state. The source texts are
the package-2 renderings: A's text from the A-state only, B's from the B-state only.

certify() checks by enumeration, for every task:
  1. the menu has one distinct option per state, and the question text is state-independent;
  2. the prompt without context is identical for every state, and the prompt with the other
     source depends on the other coordinate only;
  3. the own-source rendering is injective and every option's literals occur in its own state's
     text and not all in any other state's text, so an ideal reader identifies the state (V* = 1);
  4. the complete decision space {1, ..., N, invalid} has acceptance sets of size at most r = 1,
     so under the uniform prior no rule that sees no information about the state exceeds r/N.
"""
import itertools
import re

import pairs as P

PAIR_IDS = ("inventory", "audit")
ARMS = ("none", "A", "B")
INSTRUCTION = ("If the information above does not settle it, choose the option you consider most "
               "likely. Reply with the option number on the last line, in the form 'Answer: <number>'.")


# ---- option texts and the literals that tie each option to its own state's documentation ------

def _inv_a(a):
    if a["order"] == "qty_first":
        sig = "inventory.reserve(qty: int, sku: str, *, %s: int)" % a["kw"]
    else:
        sig = "inventory.reserve(sku: str, qty: int, *, %s: int)" % a["kw"]
    exc = "inventory.%s" % a["exc"]
    return "`%s`; when stock is short it raises `%s`" % (sig, exc), [sig, exc]


def _inv_b(b):
    mod, letters = b["check"].split(":")
    text = ("zero-pad the item number to %d digits, prefix '%s', then append '.' and a check letter: "
            "the digit sum modulo %s used as an index into '%s'" % (b["width"], b["prefix"], mod[3:], letters))
    return text, ["%d digits" % b["width"], "'%s'" % b["prefix"], "modulo %s" % mod[3:], "'%s'" % letters]


def _audit_a(a):
    t = P.AUDIT_TABLES[a["table"]]
    text = ("'granted' -> '%s', 'denied' -> '%s', 'expired' -> '%s', 'locked' -> '%s', any other "
            "reason -> '%s'" % (t["granted"], t["denied"], t["expired"], t["locked"], t["other"]))
    return text, ["'%s'" % t[k] for k in ("granted", "denied", "expired", "locked", "other")]


def _audit_b(b):
    case = "UPPER case" if b["user"] == "upper" else "lower case"
    base = "hexadecimal" if b["epoch"] == "hex" else "octal"
    text = ("user name in %s, separator '%s', action name written backwards, epoch seconds in %s"
            % (case, b["sep"], base))
    return text, [case, "separator '%s'" % b["sep"], base]


TASKS = {
    ("inventory", "A"): {"id": "inv_contract_label", "option": _inv_a, "question": (
        "Question: in our team's `inventory` module, which of the following is the canonical call of "
        "`inventory.reserve` together with the exception it raises when stock is short?")},
    ("inventory", "B"): {"id": "inv_sku_label", "option": _inv_b, "question": (
        "Question: in our team's `inventory` module, which of the following is the rule that turns an "
        "item number into a SKU code?")},
    ("audit", "A"): {"id": "audit_code_label", "option": _audit_a, "question": (
        "Question: in our team's `audit` module, which of the following is the table of private status "
        "codes for access decisions?")},
    ("audit", "B"): {"id": "audit_line_label", "option": _audit_b, "question": (
        "Question: in our team's `audit` module, which of the following is the audit log line format?")},
}


def space(pid, x):
    p = P.PAIRS[pid]
    return p["A_space"] if x == "A" else p["B_space"]


def menu_states(pid, x):
    return P.states(space(pid, x))


def options(pid, x):
    return [TASKS[(pid, x)]["option"](s)[0] for s in menu_states(pid, x)]


def question(pid, x):
    """The state-independent part of every prompt of the X-label task."""
    t = TASKS[(pid, x)]
    lines = [t["question"], "Options:"] + ["%d. %s" % (i + 1, o) for i, o in enumerate(options(pid, x))]
    return "\n".join(lines + [INSTRUCTION])


def truth(pid, x, a_state, b_state):
    """The correct option number (1-based) for the hidden state."""
    s = a_state if x == "A" else b_state
    return menu_states(pid, x).index(s) + 1


def context(pid, arm, a_state, b_state):
    p = P.PAIRS[pid]
    if arm == "none":
        return None
    return p["render_a"](a_state) if arm == "A" else p["render_b"](b_state)


def prompt(pid, x, arm, a_state, b_state):
    ctx = context(pid, arm, a_state, b_state)
    q = question(pid, x)
    return (ctx + "\n\n" + q) if ctx else q


_ANSWER = re.compile(r"answer\s*[:\-]\s*[*_`\s]*(\d+)", re.I)


def parse_choice(text, n_options):
    """The option number a reply chose, or None (an invalid decision, accepted under no state).
    Rule fixed in advance: the last 'Answer: <number>' in the reply; otherwise a reply that is a
    bare number; numbers outside 1..N are invalid."""
    text = text or ""
    found = _ANSWER.findall(text)
    if found:
        k = int(found[-1])
    else:
        bare = text.strip().strip("*_`. ")
        if not bare.isdigit():
            return None
        k = int(bare)
    return k if 1 <= k <= n_options else None


def grade(text, pid, x, a_state, b_state):
    n = len(menu_states(pid, x))
    c = parse_choice(text, n)
    return {"choice": c, "correct": c is not None and c == truth(pid, x, a_state, b_state)}


def caps():
    return {TASKS[(pid, x)]["id"]: 1.0 / len(menu_states(pid, x)) for pid in PAIR_IDS for x in ("A", "B")}


def certify():
    """Enumeration checks 1-4 of the module docstring; returns {task id: report}, raises on failure."""
    out = {}
    for pid in PAIR_IDS:
        p = P.PAIRS[pid]
        a_all, b_all = P.states(p["A_space"]), P.states(p["B_space"])
        for x in ("A", "B"):
            tid = TASKS[(pid, x)]["id"]
            own = a_all if x == "A" else b_all
            render = p["render_a"] if x == "A" else p["render_b"]
            opts = options(pid, x)
            n = len(own)
            # 1. one distinct option per state; question independent of the state (built without it)
            assert len(opts) == n and len(set(opts)) == n, (tid, "options not distinct")
            q = question(pid, x)
            assert q == question(pid, x)
            # 2. prompts: none is constant; the other-source prompt depends on the other coordinate only
            other = "B" if x == "A" else "A"
            none_prompts, other_by_coord = set(), {}
            for a, b in itertools.product(a_all, b_all):
                none_prompts.add(prompt(pid, x, "none", a, b))
                key = P.key_of(b if other == "B" else a)
                other_by_coord.setdefault(key, set()).add(prompt(pid, x, other, a, b))
            assert len(none_prompts) == 1, (tid, "no-context prompt varies with the state")
            assert all(len(v) == 1 for v in other_by_coord.values()), (tid, "other-source prompt varies with this task's state")
            # 3. injective own rendering; option literals in their own text and not all in any other text
            texts = [render(s) for s in own]
            assert len(set(texts)) == n, (tid, "own rendering not injective")
            for i, s in enumerate(own):
                lits = TASKS[(pid, x)]["option"](s)[1]
                assert all(l in texts[i] for l in lits), (tid, "option literal missing from its own text", P.key_of(s))
                for j, t in enumerate(texts):
                    if j != i:
                        assert not all(l in t for l in lits), (tid, "option literals all present in another state's text")
            # ideal reader: identify the state from the text by matching renderings; always correct
            reader = {t: i + 1 for i, t in enumerate(texts)}
            for a, b in itertools.product(a_all, b_all):
                ctx = context(pid, x, a, b)
                assert reader[ctx] == truth(pid, x, a, b)
            # 4. complete decision space {1..N, invalid}: acceptance-set sizes
            acc = {d: sum(1 for s in own if menu_states(pid, x).index(s) + 1 == d) for d in range(1, n + 1)}
            acc["invalid"] = 0
            r = max(acc.values())
            assert r == 1
            out[tid] = {"pair": pid, "source": x, "states": n, "max_acceptance_set": r, "cap_uniform_prior": r / n,
                        "prompt_none_constant": True, "other_prompt_depends_on_other_coordinate_only": True,
                        "own_rendering_injective": True, "ideal_reader_value": 1.0}
    # parser checks (state-independent)
    assert parse_choice("Reasoning...\nAnswer: 3", 8) == 3
    assert parse_choice("**Answer:** 2", 8) == 2
    assert parse_choice("4", 8) == 4
    assert parse_choice("Answer: 9", 8) is None
    assert parse_choice("I think option 2", 8) is None
    return out
