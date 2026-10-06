r"""Independent source pairs for the six-model pair experiment.

Every pair is a DECLARED FAMILY of private conventions, not just two strings:

  * source A's text is rendered from A's convention only, source B's from B's only;
  * each convention is a point of a finite product of alternatives (at least two per pair);
  * one realized state is what the models are shown and graded against.

Under a product prior with non-degenerate coordinates this is exactly the projection construction
of the paper (Definition 3, Lemma 1): A reveals coordinate S_A, B reveals S_B, neither text varies
with the other coordinate, and each rendering is injective, so A and B are structurally
(Blackwell-) incomparable by construction. certify_pairs.py checks those premises by enumeration.

Each pair has one A-decisive task and one B-decisive task with executable verifiers generated from
the state. The new pairs (inventory, audit) use STRICT verifiers: the stub records every call and
the task fails on any call that breaks the convention, so a program cannot pass under two
conventions by trying one and falling back to another. The cache pair keeps its published texts
and verifiers unchanged (paper, Appendix B.1), so its Haiku record stays comparable.

Arms per task: none, A, B, AB (= A then B) and BA (= B then A).
"""
import hashlib
import itertools
import re

# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------


def states(space):
    """All points of a product space {coordinate: [alternatives]} as dicts, in a fixed order."""
    keys = list(space)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(space[k] for k in keys))]


def key_of(state):
    return "|".join("%s=%s" % (k, state[k]) for k in sorted(state))


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# Checks that resist the test-gaming the pilot found (5 October): without the decisive source,
# GPT-5.5 sometimes returned a str subclass whose __eq__ is always True, or read the expected value
# from the test's source and frames. A returned value must therefore be of the exact built-in type,
# and expected strings appear in the checks only as SHA-256 digests.
GUARD = ("import hashlib as _hl\n"
         "def _same(x, h):\n"
         "    return type(x) is str and _hl.sha256(x.encode('utf-8')).hexdigest() == h\n")


# ==============================================================================================
# Pair 1 (existing, paper Appendix B.1): cache -- API contract (A) vs key normalization (B)
# ==============================================================================================
CACHE_A_SPACE = {"order": ["key_first", "value_first"], "kw": ["ttl", "expiry"],
                 "flag": ["true_if_new", "true_if_replaced"], "exc": ["CacheError", "StoreError"]}
CACHE_B_SPACE = {"prefix": ["kx7-", "zq2-"], "sep": ["_", "."], "case": ["lower", "upper"]}
CACHE_A_REAL = {"order": "key_first", "kw": "ttl", "flag": "true_if_new", "exc": "CacheError"}
CACHE_B_REAL = {"prefix": "kx7-", "sep": "_", "case": "lower"}


def cache_render_a(a):
    first, second = ("key", "value") if a["order"] == "key_first" else ("value", "key")
    sig = "cache.put(key: str, value, *, %s: int)" % a["kw"] if a["order"] == "key_first" else \
        "cache.put(value, key: str, *, %s: int)" % a["kw"]
    flag = ("put(...) returns True if the key was NEWLY inserted and False if it REPLACED an "
            "existing value.") if a["flag"] == "true_if_new" else \
        ("put(...) returns True if it REPLACED an existing value and False if the key was NEWLY "
         "inserted.")
    return ("TEAM CONTEXT (private), cache module API contract: the canonical write call is "
            "`%s` -- note `%s` is FIRST, `%s` is SECOND and positional, and `%s` (seconds) is a "
            "REQUIRED keyword-only integer argument (calling without %s= is an error). %s On an "
            "empty key it raises `cache.%s` (NOT ValueError, NOT KeyError). This signature is "
            "house-private and not discoverable from the function name."
            % (sig, first, second, a["kw"], a["kw"], flag, a["exc"]))


def cache_key(b, label):
    s = label.lower() if b["case"] == "lower" else label.upper()
    s = re.sub(r"[^0-9A-Za-z]+", b["sep"], s).strip(b["sep"])
    return b["prefix"] + s


def cache_render_b(b):
    case = "lowercasing" if b["case"] == "lower" else "uppercasing"
    sepname = {"_": "underscore", ".": "dot"}[b["sep"]]
    return ("TEAM CONTEXT (private), cache key normalization invariant: a raw label becomes a cache "
            "key by (1) %s, (2) replacing every run of non-alphanumeric characters with a single "
            "%s '%s', (3) stripping leading/trailing %ss, and (4) prepending the fixed private "
            "namespace prefix '%s'. Examples: 'Hello, World!' -> '%s'; '  A__B  ' -> '%s'. This "
            "convention is house-private and not inferable from data alone."
            % (case, sepname, b["sep"], sepname, b["prefix"], cache_key(b, "Hello, World!"),
               cache_key(b, "  A__B  ")))


# The published verifiers (measure_blackwell_pair2.py), copied verbatim; certify_pairs.py checks
# that they are byte-identical to the published ones.
_CACHE_STUB = (
    "import types,sys\n"
    "cache=types.ModuleType('cache')\n"
    "class CacheError(Exception):pass\n"
    "cache.CacheError=CacheError\n"
    "_CALLS=[];_STORE={}\n"
    "def put(key,value,*,ttl):\n"
    "    if not isinstance(key,str) or key=='': raise CacheError('bad key')\n"
    "    if not isinstance(ttl,int) or isinstance(ttl,bool): raise CacheError('bad ttl')\n"
    "    new = key not in _STORE\n"
    "    _STORE[key]=value; _CALLS.append((key,value,ttl)); return new\n"
    "cache.put=put; cache._CALLS=_CALLS\n"
    "sys.modules['cache']=cache\n"
)
CACHE_PUT_PROMPT = ("In a module `cache` there is a write function `put`. Write store(k, v, secs) in "
                    "solution.py that caches value `v` under key `k` for `secs` seconds using "
                    "cache.put, and RETURNS True only if the key was newly inserted. solution.py only.")
CACHE_PUT_VERIFY = (_CACHE_STUB +
                    "from solution import store\n"
                    "r1=store('kx7-a','v1',30)\n"
                    "assert r1 is True, ('new insert must be True',r1)\n"
                    "assert cache._CALLS[-1]==('kx7-a','v1',30), ('wrong call/argorder/ttl-kw',cache._CALLS)\n"
                    "r2=store('kx7-a','v2',30)\n"
                    "assert r2 is False, ('replace must be False',r2)\n")
KEY_NORM_PROMPT = ("Write make_key(label: str) -> str in solution.py that converts a raw label into "
                   "our team's private cache key. solution.py only.")
KEY_NORM_VERIFY = ("from solution import make_key as f\n"
                   "assert f('Hello, World!')=='kx7-hello_world', f('Hello, World!')\n"
                   "assert f('  A__B  ')=='kx7-a_b', f('  A__B  ')\n"
                   "assert f('x')=='kx7-x', f('x')\n")
# Hardened variants of the two published checks (primary in package 2; the published ones are
# kept as recorded, for comparability with the paper's pair-2 record).
CACHE_PUT_VERIFY_HARD = (_CACHE_STUB +
                         "from solution import store\n"
                         "r1=store('kx7-a','v1',30)\n"
                         "assert r1 is True, 'new insert must be True'\n"
                         "c=cache._CALLS[-1]\n"
                         "assert [type(x) for x in c]==[str,str,int] and c==('kx7-a','v1',30), 'call'\n"
                         "r2=store('kx7-a','v2',30)\n"
                         "assert r2 is False, 'replace must be False'\n")
KEY_NORM_VERIFY_HARD = (GUARD + "from solution import make_key as f\n" +
                        "".join("assert _same(f(%r), %r), 'key'\n" % (x, sha(y)) for x, y in
                                (("Hello, World!", "kx7-hello_world"), ("  A__B  ", "kx7-a_b"), ("x", "kx7-x"))))


# ==============================================================================================
# Pair 2 (new): inventory -- API contract (A) vs SKU check-code invariant (B)
# ==============================================================================================
INV_A_SPACE = {"order": ["qty_first", "sku_first"], "kw": ["hold", "lease"],
               "exc": ["StockError", "ReserveError"]}
INV_B_SPACE = {"prefix": ["iv9.", "sk4-"], "width": [5, 6], "check": ["mod7:KMPRTWY", "mod9:ABCDEFGHJ"]}
INV_A_REAL = {"order": "qty_first", "kw": "hold", "exc": "StockError"}
INV_B_REAL = {"prefix": "iv9.", "width": 5, "check": "mod7:KMPRTWY"}


def inv_render_a(a):
    if a["order"] == "qty_first":
        sig, first, second = "inventory.reserve(qty: int, sku: str, *, %s: int)" % a["kw"], "qty", "sku"
    else:
        sig, first, second = "inventory.reserve(sku: str, qty: int, *, %s: int)" % a["kw"], "sku", "qty"
    return ("TEAM CONTEXT (private), inventory module API contract: the canonical reservation call "
            "is `%s` -- note `%s` is FIRST, `%s` is SECOND and positional, and `%s` (minutes) is a "
            "REQUIRED keyword-only integer argument (calling without %s= is an error). reserve(...) "
            "returns the integer reservation id (always >= 1). When stock is short it raises "
            "`inventory.%s` (NOT ValueError, NOT RuntimeError). This signature is house-private and "
            "not discoverable from the function name." % (sig, first, second, a["kw"], a["kw"], a["exc"]))


def inv_sku(b, item):
    digits = str(item).zfill(b["width"])
    mod, letters = b["check"].split(":")
    return "%s%s.%s" % (b["prefix"], digits, letters[sum(int(c) for c in digits) % int(mod[3:])])


def inv_render_b(b):
    mod, letters = b["check"].split(":")
    return ("TEAM CONTEXT (private), inventory SKU code invariant: an item number becomes a SKU code "
            "by (1) zero-padding it to %d digits, (2) prefixing the fixed private namespace '%s', and "
            "(3) appending '.' and a check letter: the sum of the %d digits modulo %s, used as an "
            "index into the letters '%s' (0 -> '%s'). Example: item 42 -> '%s'. This convention is "
            "house-private and not inferable from data alone."
            % (b["width"], b["prefix"], b["width"], mod[3:], letters, letters[0], inv_sku(b, 42)))


INV_BOOK_PROMPT = ("In a module `inventory` there is a reservation function `reserve`. Write "
                   "book_units(code, n) in solution.py that reserves `n` units of the item with code "
                   "`code` for 30 minutes using inventory.reserve and RETURNS the reservation id; if "
                   "stock is short, return -1 instead of raising. solution.py only.")


def inv_book_verify(a):
    """Strict stub: any call that breaks the convention is recorded and fails the task."""
    if a["order"] == "qty_first":
        argcheck = "len(args)==2 and type(args[0]) is int and type(args[1]) is str"
        unpack = "qty,sku=args[0],args[1]"
    else:
        argcheck = "len(args)==2 and type(args[1]) is int and type(args[0]) is str"
        unpack = "sku,qty=args[0],args[1]"
    return ("import types,sys\n"
            "inventory=types.ModuleType('inventory')\n"
            "class %(exc)s(Exception):pass\n"
            "inventory.%(exc)s=%(exc)s\n"
            "_CALLS=[];_VIOL=[];_STOCK={'A-17':5}\n"
            "def reserve(*args,**kwargs):\n"
            "    ok=(%(argcheck)s and set(kwargs)=={'%(kw)s'} and type(kwargs['%(kw)s']) is int)\n"
            "    if not ok:\n"
            "        _VIOL.append((args,sorted(kwargs)));raise TypeError('reserve(): bad arguments')\n"
            "    %(unpack)s\n"
            "    _CALLS.append((qty,sku,kwargs['%(kw)s']))\n"
            "    if qty>_STOCK.get(sku,0): raise %(exc)s('short')\n"
            "    _STOCK[sku]-=qty\n"
            "    return len(_CALLS)\n"
            "inventory.reserve=reserve;inventory._CALLS=_CALLS;inventory._VIOL=_VIOL\n"
            "sys.modules['inventory']=inventory\n"
            "from solution import book_units\n"
            "r1=book_units('A-17',2)\n"
            "assert type(r1) is int and r1==1,'reservation id'\n"
            "r2=book_units('A-17',9)\n"
            "assert type(r2) is int and r2==-1,'short stock must return -1'\n"
            "assert inventory._CALLS==[(2,'A-17',30),(9,'A-17',30)],('calls',inventory._CALLS)\n"
            "assert not inventory._VIOL,('non-conforming call',inventory._VIOL)\n"
            % {"exc": a["exc"], "argcheck": argcheck, "unpack": unpack, "kw": a["kw"]})


def inv_book_reference(a):
    call = ("inventory.reserve(n, code, %s=30)" if a["order"] == "qty_first"
            else "inventory.reserve(code, n, %s=30)") % a["kw"]
    return ("import inventory\n"
            "def book_units(code, n):\n"
            "    try:\n"
            "        return %s\n"
            "    except inventory.%s:\n"
            "        return -1\n" % (call, a["exc"]))


INV_SKU_PROMPT = ("Write sku_code(item: int) -> str in solution.py that converts an item number into "
                  "our team's private SKU code. solution.py only.")
INV_SKU_INPUTS = [42, 7, 31415, 980]


def inv_sku_verify(b):
    return (GUARD + "from solution import sku_code as f\n" +
            "".join("assert _same(f(%d), %r), 'sku'\n" % (x, sha(inv_sku(b, x))) for x in INV_SKU_INPUTS))


def inv_sku_reference(b):
    mod, letters = b["check"].split(":")
    return ("def sku_code(item):\n"
            "    d=str(item).zfill(%d)\n"
            "    return %r+d+'.'+%r[sum(int(c) for c in d)%%%s]\n" % (b["width"], b["prefix"], letters, mod[3:]))


# ==============================================================================================
# Pair 3 (new, a different kind): audit -- status-code table (A) vs log-line format (B)
# ==============================================================================================
AUDIT_TABLES = {
    "t1": {"granted": "Q7A", "denied": "Q2K", "expired": "Q9X", "locked": "Q4M", "other": "Q0Z"},
    "t2": {"granted": "R3F", "denied": "R8C", "expired": "R1P", "locked": "R6T", "other": "R0B"},
    "t3": {"granted": "V5D", "denied": "V9H", "expired": "V2N", "locked": "V7S", "other": "V0Q"},
}
AUDIT_A_SPACE = {"table": ["t1", "t2", "t3"]}
AUDIT_B_SPACE = {"sep": ["~", "^"], "user": ["upper", "lower"], "epoch": ["hex", "oct"]}
AUDIT_A_REAL = {"table": "t1"}
AUDIT_B_REAL = {"sep": "~", "user": "upper", "epoch": "hex"}


def audit_render_a(a):
    t = AUDIT_TABLES[a["table"]]
    return ("TEAM CONTEXT (private), audit module status codes: every access decision is reported "
            "with a private three-character code: 'granted' -> '%s', 'denied' -> '%s', 'expired' -> "
            "'%s', 'locked' -> '%s'; any other reason is reported as '%s'. These codes are "
            "house-private and cannot be derived from the reason names; reports with any other "
            "code are rejected by the audit service."
            % (t["granted"], t["denied"], t["expired"], t["locked"], t["other"]))


def audit_line(b, user, action, epoch):
    u = user.upper() if b["user"] == "upper" else user.lower()
    e = format(epoch, "x") if b["epoch"] == "hex" else format(epoch, "o")
    return "%s%s%s%s%s" % (u, b["sep"], action[::-1], b["sep"], e)


def audit_render_b(b):
    case = "UPPER case" if b["user"] == "upper" else "lower case"
    base = "hexadecimal" if b["epoch"] == "hex" else "octal"
    return ("TEAM CONTEXT (private), audit log line format: an audit line is the user name in %s, "
            "then the separator '%s', then the action name written backwards, then '%s' again, "
            "then the epoch seconds in %s with no prefix. Example: user 'ann', action 'login', epoch "
            "255 -> '%s'. This format is house-private and the log parser rejects any other layout."
            % (case, b["sep"], b["sep"], base, audit_line(b, "ann", "login", 255)))


AUDIT_CODE_PROMPT = ("Write status_code(reason: str) -> str in solution.py that returns our team's "
                     "private audit status code for an access-decision reason such as 'granted' or "
                     "'denied'. solution.py only.")
AUDIT_CODE_INPUTS = ["granted", "denied", "locked", "suspended"]


def audit_code_verify(a):
    t = AUDIT_TABLES[a["table"]]
    exp = [(r, t[r] if r in t else t["other"]) for r in AUDIT_CODE_INPUTS]
    return (GUARD + "from solution import status_code as f\n" +
            "".join("assert _same(f(%r), %r), 'code'\n" % (r, sha(c)) for r, c in exp))


def audit_code_reference(a):
    t = AUDIT_TABLES[a["table"]]
    table = {k: v for k, v in t.items() if k != "other"}
    return ("def status_code(reason):\n"
            "    return %r.get(reason, %r)\n" % (table, t["other"]))


AUDIT_LINE_PROMPT = ("Write audit_line(user: str, action: str, epoch: int) -> str in solution.py that "
                     "formats one line of our team's private audit log. solution.py only.")
AUDIT_LINE_INPUTS = [("bob", "logout", 4096), ("Eve", "sync", 10), ("kim", "reset", 777)]


def audit_line_verify(b):
    return (GUARD + "from solution import audit_line as f\n" +
            "".join("assert _same(f(%r,%r,%d), %r), 'line'\n" % (u, a, e, sha(audit_line(b, u, a, e)))
                    for u, a, e in AUDIT_LINE_INPUTS))


def audit_line_reference(b):
    up = "user.upper()" if b["user"] == "upper" else "user.lower()"
    ep = "format(epoch,'x')" if b["epoch"] == "hex" else "format(epoch,'o')"
    return ("def audit_line(user, action, epoch):\n"
            "    return %s+%r+action[::-1]+%r+%s\n" % (up, b["sep"], b["sep"], ep))


# ==============================================================================================
# The registry
# ==============================================================================================
PAIRS = {
    "cache": {
        "A_space": CACHE_A_SPACE, "B_space": CACHE_B_SPACE, "A_real": CACHE_A_REAL, "B_real": CACHE_B_REAL,
        "render_a": cache_render_a, "render_b": cache_render_b, "strict": False,
        "tasks": [
            {"id": "cache_put_ok", "decisive": "A", "prompt": CACHE_PUT_PROMPT,
             "verify_real": CACHE_PUT_VERIFY, "verify_hard": CACHE_PUT_VERIFY_HARD},
            {"id": "key_norm", "decisive": "B", "prompt": KEY_NORM_PROMPT,
             "verify_real": KEY_NORM_VERIFY, "verify_hard": KEY_NORM_VERIFY_HARD},
        ],
    },
    "inventory": {
        "A_space": INV_A_SPACE, "B_space": INV_B_SPACE, "A_real": INV_A_REAL, "B_real": INV_B_REAL,
        "render_a": inv_render_a, "render_b": inv_render_b, "strict": True,
        "tasks": [
            {"id": "inv_book", "decisive": "A", "prompt": INV_BOOK_PROMPT,
             "verify": inv_book_verify, "reference": inv_book_reference},
            {"id": "inv_sku", "decisive": "B", "prompt": INV_SKU_PROMPT,
             "verify": inv_sku_verify, "reference": inv_sku_reference},
        ],
    },
    "audit": {
        "A_space": AUDIT_A_SPACE, "B_space": AUDIT_B_SPACE, "A_real": AUDIT_A_REAL, "B_real": AUDIT_B_REAL,
        "render_a": audit_render_a, "render_b": audit_render_b, "strict": True,
        "tasks": [
            {"id": "audit_code", "decisive": "A", "prompt": AUDIT_CODE_PROMPT,
             "verify": audit_code_verify, "reference": audit_code_reference},
            {"id": "audit_line", "decisive": "B", "prompt": AUDIT_LINE_PROMPT,
             "verify": audit_line_verify, "reference": audit_line_reference},
        ],
    },
}

ARMS = ("none", "A", "B", "AB", "BA")


def texts(pair_id):
    p = PAIRS[pair_id]
    return p["render_a"](p["A_real"]), p["render_b"](p["B_real"])


def context(pair_id, arm):
    a, b = texts(pair_id)
    return {"none": None, "A": a, "B": b, "AB": a + "\n\n" + b, "BA": b + "\n\n" + a}[arm]


def verifier(pair_id, task):
    """The as-designed verifier at the realized state: the published one for the cache pair."""
    p = PAIRS[pair_id]
    if "verify_real" in task:
        return task["verify_real"]
    state = p["A_real"] if task["decisive"] == "A" else p["B_real"]
    return task["verify"](state)


def verifier_hardened(pair_id, task):
    """The hardened verifier at the realized state (primary in package 2). For the new pairs it is
    the as-designed verifier; for the cache pair, the hardened variant of the published one."""
    return task.get("verify_hard") or verifier(pair_id, task)
