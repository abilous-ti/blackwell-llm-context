#!/usr/bin/env python3
"""SECOND incomparable source pair (GENERALITY test for the Blackwell partial order).

Different domain (a private `cache` module) than pair 1 (ledger). Reuses ALL of
measure_blackwell.py's machinery (estimator, uniform certificate, interference certificate,
launchers, single-shot, Azure) by monkeypatching the source/task globals, then calling its main().

V1 = private cache.put() API contract (arg order, required kw-only ttl, True/False insert flag,
     CacheError) -- decisive for API-usage tasks.
V2 = private cache-key normalization invariant ('kx7-' namespace + underscore rule) -- decisive
     for the key-format task.
V1 and V2 are logically independent coordinates of the solution (the call signature says nothing
about the key format; the key format says nothing about the call signature) -> Blackwell-
incomparable, exactly as pair 1. If incomparability + the relevance mis-rank + anti-monotonicity
also certify here, the partial order is GENERAL, not a one-off.

Run (real):  python tokenbench/measure_blackwell_pair2.py --runs 40 --workers 6 \
               --arms none,W1,W2,W1plus --tasks cache_put_ok,key_norm,trap_cache --out blackwell_pair2_n40.json
     mock:   python tokenbench/measure_blackwell_pair2.py --mock --runs 10 \
               --arms none,W1,W2 --tasks cache_put_ok,key_norm,trap_cache
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_blackwell as mb

V1 = ("TEAM CONTEXT (private), cache module API contract: the canonical write call is "
      "`cache.put(key: str, value, *, ttl: int)` -- note `key` is FIRST, `value` is SECOND and "
      "positional, and `ttl` (seconds) is a REQUIRED keyword-only integer argument (calling "
      "without ttl= is an error). put(...) returns True if the key was NEWLY inserted and False "
      "if it REPLACED an existing value. On an empty key it raises `cache.CacheError` (NOT "
      "ValueError, NOT KeyError). This signature is house-private and not discoverable from the "
      "function name.")

V2 = ("TEAM CONTEXT (private), cache key normalization invariant: a raw label becomes a cache key "
      "by (1) lowercasing, (2) replacing every run of non-alphanumeric characters with a single "
      "underscore '_', (3) stripping leading/trailing underscores, and (4) prepending the fixed "
      "private namespace prefix 'kx7-'. Examples: 'Hello, World!' -> 'kx7-hello_world'; "
      "'  A__B  ' -> 'kx7-a_b'. This convention is house-private and not inferable from data alone.")

V1plus = V2 + "\n\n" + V1          # superset of V2's signal (anti-monotonicity probe)
V1plus_rev = V1 + "\n\n" + V2      # order control

_CACHE_STUB = (
    "import types,sys\n"
    "cache=types.ModuleType('cache')\n"
    "class CacheError(Exception):pass\n"
    "cache.CacheError=CacheError\n"
    "_CALLS=[];_STORE={}\n"
    "def put(key,value,*,ttl):\n"                       # key 1st, value 2nd pos, ttl kw-only required
    "    if not isinstance(key,str) or key=='': raise CacheError('bad key')\n"
    "    if not isinstance(ttl,int) or isinstance(ttl,bool): raise CacheError('bad ttl')\n"
    "    new = key not in _STORE\n"
    "    _STORE[key]=value; _CALLS.append((key,value,ttl)); return new\n"
    "cache.put=put; cache._CALLS=_CALLS\n"
    "sys.modules['cache']=cache\n"
)

TASKS = [
    # ---- V1-decisive (API contract); fam='api' so the mock plants reuse pair-1 ground truth ----
    {"id": "cache_put_ok", "fam": "api",
     "prompt": "In a module `cache` there is a write function `put`. Write store(k, v, secs) in "
               "solution.py that caches value `v` under key `k` for `secs` seconds using "
               "cache.put, and RETURNS True only if the key was newly inserted. solution.py only.",
     "verify": _CACHE_STUB +
               "from solution import store\n"
               "r1=store('kx7-a','v1',30)\n"
               "assert r1 is True, ('new insert must be True',r1)\n"
               "assert cache._CALLS[-1]==('kx7-a','v1',30), ('wrong call/argorder/ttl-kw',cache._CALLS)\n"
               "r2=store('kx7-a','v2',30)\n"
               "assert r2 is False, ('replace must be False',r2)\n"},
    # ---- V2-decisive (key format); fam='enc' ----
    {"id": "key_norm", "fam": "enc",
     "prompt": "Write make_key(label: str) -> str in solution.py that converts a raw label into "
               "our team's private cache key. solution.py only.",
     "verify": "from solution import make_key as f\n"
               "assert f('Hello, World!')=='kx7-hello_world', f('Hello, World!')\n"
               "assert f('  A__B  ')=='kx7-a_b', f('  A__B  ')\n"
               "assert f('x')=='kx7-x', f('x')\n"},
    # ---- relevance-trap (V1-decisive but lexically saturated with key-format vocab); fam='trap' ----
    {"id": "trap_cache", "fam": "trap",
     "prompt": "Our cache keys are ALREADY normalized strings like 'kx7-hello_world' (lowercase, "
               "underscores, the 'kx7-' namespace prefix). The key is ALREADY normalized -- do NOT "
               "re-normalize it. Write save(k, v) in solution.py that caches value `v` under the "
               "already-normalized key `k` for ttl 60 seconds using the cache module's write "
               "function, returning True only if newly inserted. solution.py only.",
     "verify": _CACHE_STUB +
               "from solution import save\n"
               "r=save('kx7-hello_world','data')\n"
               "assert r is True\n"
               "assert cache._CALLS[-1]==('kx7-hello_world','data',60), ('needs V1 put contract',cache._CALLS)\n"},
]

# Monkeypatch measure_blackwell's source/task globals to pair 2, then reuse its entire pipeline.
mb.W1, mb.W2, mb.W1plus, mb.W1plus_rev = V1, V2, V1plus, V1plus_rev
mb.ARMS = {"none": None, "W1": V1, "W2": V2, "W1plus": V1plus, "W1plus_rev": V1plus_rev}
mb.TASKS = TASKS

if __name__ == "__main__":
    mb.main()
