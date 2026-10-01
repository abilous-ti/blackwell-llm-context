r"""The published harness's HTTP request, sent unchanged, with the response metadata it discarded kept.

build_request() constructs exactly the request harness/measure_blackwell.py::_azure_complete sends
(test_replication.py checks URL, method, headers and body byte for byte). post() adds what the
original client threw away: the model field the endpoint returns, the response id, the full usage
block, the stop reason, the rest of the response envelope, the HTTP status and the time of every
attempt. The retry rule is the
original one: up to three attempts, 2 s and 4 s apart, on any exception from the request or from
parsing its JSON. A response that parses is never retried, whatever it contains.
"""
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def build_request(prompt, model, endpoint, key):
    if "anthropic" in endpoint:   # Anthropic Messages API (also served by Azure AI Foundry)
        url = endpoint
        headers = {"Content-Type": "application/json", "x-api-key": key, "api-key": key,
                   "anthropic-version": "2023-06-01"}
        body = {"model": model, "max_tokens": 8000,
                "messages": [{"role": "user", "content": prompt}]}
    elif "responses" in endpoint:
        url, headers = endpoint, {"Content-Type": "application/json", "api-key": key}
        body = {"model": model, "input": prompt, "max_output_tokens": 8000}
    else:  # OpenAI-compatible chat completions
        _e = endpoint.rstrip("/")
        url = _e if _e.endswith("/chat/completions") else _e + "/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer " + key, "api-key": key}
        body = {"model": model, "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8000}
    return urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                  headers=headers)


def parse_response(out):
    """Text and output tokens exactly as the original client derives them, plus metadata."""
    if isinstance(out.get("content"), list):           # Anthropic Messages API
        text = "".join(c.get("text", "") for c in out["content"] if c.get("type") == "text")
        otoks = (out.get("usage", {}) or {}).get("output_tokens", 0)
        stop = out.get("stop_reason")
    elif "output" in out:                              # Responses API
        text = ""
        for item in out.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") in ("output_text", "text"):
                        text += c.get("text", "")
        text = text or out.get("output_text", "") or ""
        otoks = (out.get("usage", {}) or {}).get("output_tokens", 0)
        stop = out.get("status")
    else:                                              # Chat Completions
        choice = (out.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or ""
        otoks = (out.get("usage", {}) or {}).get("completion_tokens", 0)
        stop = choice.get("finish_reason")
    return {"text": text, "output_tokens": otoks, "returned_model": out.get("model"),
            "response_id": out.get("id"), "usage": out.get("usage"), "stop_reason": stop}


def envelope(out, text):
    """The whole parsed response, with the reply text (stored once, as raw_text) replaced by a
    marker, so provider fields nobody asked for (a backend fingerprint, a creation time, filter
    annotations, reasoning fields) are kept too."""
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items()}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return "<raw_text>" if isinstance(x, str) and text and x == text else x
    return strip(out)


def post(prompt, model, endpoint, key, max_attempts=3, backoff=(2, 4), timeout=180,
         allow_attempt=None):
    """One draw: returns the parsed response and an attempt log. transport_failed is True only if
    every attempt made raised; the draw is then a missing observation, not a failure.
    allow_attempt, if given, is asked before every attempt (the global call budget); when it refuses,
    no further attempt is made and budget_stop is set. A draw refused before its first attempt was
    never requested: attempts is empty and the caller records it as not collected."""
    req = build_request(prompt, model, endpoint, key)
    attempts = []
    for attempt in range(max_attempts):
        if allow_attempt is not None and not allow_attempt():
            return {"text": None, "output_tokens": None, "returned_model": None,
                    "response_id": None, "usage": None, "stop_reason": None,
                    "response": None, "attempts": attempts, "transport_failed": bool(attempts),
                    "budget_stop": True}
        start = utc_now()
        status = None
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                out = json.loads(resp.read().decode("utf-8"))
            attempts.append({"attempt": attempt + 1, "start_utc": start, "end_utc": utc_now(),
                             "http_status": status, "error": None})
            parsed = parse_response(out)
            return dict(parsed, response=envelope(out, parsed["text"]), attempts=attempts,
                        transport_failed=False, budget_stop=False)
        except Exception as e:  # noqa: BLE001 - the original client retried on any exception
            body = None
            if isinstance(e, urllib.error.HTTPError):
                status = e.code
                try:                                   # the provider's own reason, e.g. a rejected parameter
                    body = e.read().decode("utf-8", "replace")[:500] or None
                except Exception:  # noqa: BLE001
                    body = None
            attempts.append({"attempt": attempt + 1, "start_utc": start, "end_utc": utc_now(),
                             "http_status": status, "error": ("%s: %s" % (type(e).__name__, e))[:300],
                             "error_body": body})
            if attempt < max_attempts - 1:
                time.sleep(backoff[min(attempt, len(backoff) - 1)])
    return {"text": None, "output_tokens": None, "returned_model": None, "response_id": None,
            "usage": None, "stop_reason": None, "response": None, "attempts": attempts,
            "transport_failed": True,
            "budget_stop": False}
