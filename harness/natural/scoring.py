r"""Deterministic scoring for the natural-data pilot. A reply PASSes when it states the gold answer.

Numbers (TAT-QA arithmetic, counts, numeric spans): every number in the reply is a candidate, with
its sign (a leading minus or parentheses) and any scale word after it (thousand, million, billion,
percent). A candidate matches if it equals the gold value as printed, or as an absolute amount
after both scales are applied, or, for a percentage, as a fraction times 100, within the gold's
printed precision or 0.5% relative error, whichever is larger.

Short spans and entity answers: the reply passes if it contains every content word of the gold (or
of one alias), or if its SQuAD token F1 with the gold reaches the threshold. Dates pass when the
reply holds the same day, month and year in any format. Yes/no answers must lead the reply.

Long spans (answers that are explanations): token F1 with the gold must reach F1_THRESHOLD (0.5),
fixed before the pilot; every F1 value is kept so the threshold can be reviewed at the freeze.
"""
import re
import string

F1_THRESHOLD = 0.5
MULT = {"": 1.0, "thousand": 1e3, "million": 1e6, "billion": 1e9, "percent": 1.0}
SCALE_WORDS = {"thousand": "thousand", "thousands": "thousand", "k": "thousand", "million": "million",
               "millions": "million", "m": "million", "mn": "million", "billion": "billion", "bn": "billion",
               "%": "percent", "percent": "percent", "per cent": "percent"}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
STOP = {"a", "an", "the", "of", "and", "to", "in", "on", "for", "from", "by", "with", "during"}


def normalize(s):
    s = str(s).lower().replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("æ", "ae").replace("ł", "l")
    s = "".join(ch if ch not in string.punctuation or ch in "-." else " " for ch in s)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.replace("-", " ").split())


def tokens(s):
    return [t.strip(".") for t in normalize(s).split() if t.strip(".")]


def f1(pred, gold):
    p, g = tokens(pred), tokens(gold)
    if not p or not g:
        return 0.0
    common = sum(min(p.count(t), g.count(t)) for t in set(g))
    if common == 0:
        return 0.0
    prec, rec = common / len(p), common / len(g)
    return 2 * prec * rec / (prec + rec)


NUM = re.compile(r"(\(?)\s*([-−]?)\s*(?:[A-Za-z]{1,3}\$|[$£€¥])?\s*(\d[\d,]*(?:\.\d+)?)\s*(\)?)\s*"
                 r"(%|per cent|percent|thousands?|millions?|billion|bn|mn|k\b|m\b)?\s*(\)?)", re.I)
NEG_WORDS = re.compile(r"\b(decrease[sd]?|declined?|declines|lower|fell|drop(ped)?|reduction|reduced|down|negative)\b", re.I)
REFUSAL = re.compile(r"\b(i (cannot|can't|can not|don't|do not|am unable|could not|couldn't)|"
                     r"(context|table|text|passage|information|data) (does not|doesn't|do not|did not) "
                     r"(contain|provide|mention|include|show|specify|state)|"
                     r"not (provided|mentioned|given|specified|stated|available|included) in the|"
                     r"no information (is|about|on|in|regarding)|cannot be (determined|calculated|answered|found))\b", re.I)
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def numbers_in(reply):
    out = []
    for m in NUM.finditer(str(reply)):
        lpar, minus, digits, rpar, scale, rpar2 = m.groups()
        try:
            v = float(digits.replace(",", ""))
        except ValueError:
            continue
        if minus or (lpar and (rpar or rpar2)):
            v = -v
        out.append((v, SCALE_WORDS.get((scale or "").lower(), "")))
    return out


def decimals(x):
    s = str(x)
    return len(s.split(".")[1]) if "." in s else 0


def close(a, b, places):
    return abs(a - b) <= max(0.005 * abs(b), 0.5 * 10 ** (-places)) + 1e-12


def numeric_gold(text):
    """A gold span that is a single number (e.g. '$1,150', '86.8', '(4.2)'), else None."""
    nums = numbers_in(text)
    stripped = re.sub(r"[\d,.$£€%()\-−\s]", "", str(text).lower())
    stripped = re.sub(r"(thousand|million|billion|percent|per cent)", "", stripped)
    return nums[0][0] if len(nums) == 1 and not stripped else None


def number_matches(reply, gold, scale):
    g, places = float(gold), decimals(gold)
    negated = g < 0 and bool(NEG_WORDS.search(str(reply)))      # "$1.32 decrease" states -1.32
    for v, sc in numbers_in(reply):
        for x in ((v, -v) if negated and v > 0 else (v,)):
            if close(x, g, places):
                return True
            if sc and close(x * MULT[sc], g * MULT.get(scale, 1.0), places):
                return True
            if scale == "percent" and not sc and close(x * 100, g, places):
                return True
            if sc == "percent" and scale != "percent" and close(x / 100, g, places):   # 87.3% for 0.87
                return True
    return False


def date_parts(s):
    t = normalize(s).replace(",", " ").split()
    year = next((x for x in t if re.fullmatch(r"\d{4}", x)), None)
    month = next((MONTHS[x] for x in t if x in MONTHS), None)
    day = next((int(x) for x in t if re.fullmatch(r"\d{1,2}", x)), None)
    return year, month, day


def span_matches(reply, gold):
    gold_n = normalize(gold)
    if gold_n in ("yes", "no"):
        return (tokens(reply) or [""])[0] == gold_n
    y, mth, d = date_parts(gold)
    if y and mth and d:
        return date_parts(reply) == (y, mth, d) or all(x in tokens(reply) for x in (y, str(d))) and \
            any(MONTHS.get(t) == mth for t in tokens(reply))
    content = [t for t in tokens(gold) if t not in STOP]
    rt = set(tokens(reply))
    return bool(content) and all(t in rt for t in content) or f1(reply, gold) >= F1_THRESHOLD


def score(reply, gold, kind, scale=""):
    """kind: 'number', 'span', 'multi', 'long' (F1), 'aliases' (list of acceptable spans).
    Returns (pass, f1_or_None)."""
    if reply is None or REFUSAL.search(str(reply)):
        return False, (None if kind != "long" else 0.0)
    if kind == "number":
        return number_matches(reply, gold, scale), None
    if kind == "long":
        g = " ".join(gold) if isinstance(gold, list) else gold
        v = f1(reply, g)
        return v >= F1_THRESHOLD, v
    if kind == "aliases":
        return any(span_matches(reply, a) for a in gold), None
    if kind == "multi":
        ok = all(number_matches(reply, numeric_gold(g), scale) if numeric_gold(g) is not None
                 else span_matches(reply, g) for g in gold)
        return ok, None
    g = gold[0] if isinstance(gold, list) else gold
    if re.fullmatch(r"\s*(?:19|20)\d{2}\s*", str(g)):            # a single year: no other year may be named
        return set(YEAR.findall(str(reply))) == {str(g).strip()}, None
    if numeric_gold(g) is not None:
        return number_matches(reply, numeric_gold(g), scale), None
    return span_matches(reply, g), None


def self_test():
    cases = [
        (("43.15%", 43.15, "number", "percent"), True), (("about 43.2 percent", 43.15, "number", "percent"), True),
        (("0.4315", 43.15, "number", "percent"), True), (("40%", 43.15, "number", "percent"), False),
        (("-10.5 million", -10.5, "number", "million"), True), (("(10.5)", -10.5, "number", "million"), True),
        (("10.5", -10.5, "number", "million"), False), (("$7,979 thousand", 7979, "number", "thousand"), True),
        (("7.979 million", 7979, "number", "thousand"), True), (("1 million", ["1"], "span", "million"), True),
        (("5", ["1"], "span", "million"), False), (("$54,000 and $3,000", ["$54,000", "$3,000"], "multi", ""), True),
        (("$54,000", ["$54,000", "$3,000"], "multi", ""), False), (("20 June 1941", ["June 20, 1941"], "aliases", ""), True),
        (("September 15, 1941", ["June 20, 1941"], "aliases", ""), False), (("Four members", ["4", "four"], "aliases", ""), True),
        (("No.", "no", "span", ""), True), (("Yes", "no", "span", ""), False), (("Ulf Merbold", "Ulf Dietrich Merbold", "span", ""), True),
        (("Chad", "Republic of Chad", "span", ""), True), (("The Legend of the Condor Heroes", ["Legend of the Condor Heroes"], "aliases", ""), True),
        (("1905 to 1928", ["1905 and 1928", "1905-1928"], "aliases", ""), True), (("Zhejiang Province", ["Zhejiang"], "aliases", ""), True),
        (("Jilin", ["Zhejiang"], "aliases", ""), False),
        # fixes from the Stage 2 manual check
        (("The average is (S$10.5 million).", -10.5, "number", "million"), True), (("87.3%", 0.87, "number", ""), True),
        (("84%", 0.87, "number", ""), False), (("$1.32 decrease", -1.32, "number", ""), True),
        (("1.32", -1.32, "number", ""), False), (("2019 and 2018", ["2018"], "span", ""), False),
        (("2018", ["2018"], "span", ""), True),
        (("I don't have information in the provided table; it covers 2019 and 2018", ["During 2019"], "span", ""), False),
    ]
    bad = [(c, want) for c, want in cases if score(c[0], c[1], c[2], c[3])[0] != want]
    return bad


if __name__ == "__main__":
    bad = self_test()
    print("scorer self-test: %s" % ("all %d cases pass" % 32 if not bad else "FAILED: %s" % bad))
