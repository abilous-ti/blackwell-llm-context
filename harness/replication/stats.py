r"""Estimators and bounds shared by the power simulation and the analysis (standard library only).

The replication's unit of analysis is the BLOCK: within one block, one model receives one request per
condition of one task, in a randomized order, back to back. For a contrast between conditions a and
b of that task, each complete block contributes d = Y_a - Y_b in {-1, 0, 1}. Blocks are independent
given the collection timeline, but they need NOT be identically distributed: success probabilities
may drift across windows. The estimand is the window-averaged effect; with the same number of blocks
in every window it equals the mean of the block differences.

Primary bound (used for every decision): Hoeffding's inequality for independent variables bounded in
[-1, 1], which requires independence but not identical distribution, so drift between windows does
not invalidate it. The window-averaged estimate weights a block of window w by 1 / (W B_w), so its
one-sided half-width at level alpha is sqrt(2 ln(1/alpha) sum_w 1/B_w) / W; with B blocks spread
equally it is sqrt(2 ln(1/alpha) / B), and missing observations that leave the windows unequal widen it.

Secondary summaries (reported, never used for decisions):
  * a window-stratified normal bound with the conservative Neyman-type variance for blocked designs,
    sum_w s_w^2 / B_w divided by W^2 (it degenerates when a window shows no variation, which is why
    it is not primary);
  * Clopper-Pearson on the pooled counts of each condition, for comparability with the original
    analysis; it treats a condition's draws as one binomial sample, which drift can violate.
"""
import math

try:  # the harness's own exact Clopper-Pearson, so the comparability column matches the paper
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from measure_blackwell import clopper_pearson  # noqa: E402
except Exception:  # pragma: no cover - the analysis never runs without the harness
    clopper_pearson = None


def hoeffding_halfwidth(n_blocks, alpha):
    """One-sided half-width for the plain mean of n independent variables bounded in [-1, 1]."""
    if n_blocks <= 0:
        return float("inf")
    return math.sqrt(2.0 * math.log(1.0 / alpha) / n_blocks)


def weighted_hoeffding_halfwidth(window_sizes, alpha):
    """One-sided half-width for the window-averaged estimate (1/W) sum_w mean_w, whose block
    weights are 1 / (W * B_w). Hoeffding (1963) for independent X_i in [a_i, b_i] gives
    t = sqrt(ln(1/alpha) * sum (b_i - a_i)^2 / 2); with ranges 2 / (W * B_w) this is
    sqrt(2 ln(1/alpha) * sum_w 1/B_w) / W, which reduces to hoeffding_halfwidth when the windows are
    equal and widens when missing observations leave them unequal."""
    sizes = [b for b in window_sizes if b > 0]
    if not sizes:
        return float("inf")
    return math.sqrt(2.0 * math.log(1.0 / alpha) * sum(1.0 / b for b in sizes)) / len(sizes)


def normal_quantile(p):
    """Acklam's rational approximation to the standard normal quantile (|error| < 1.2e-9)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    lo, hi = 0.02425, 1 - 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > hi:
        return -normal_quantile(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def contrast_summary(diffs_by_window, alpha, direction, margin=None, planned_windows=None):
    """diffs_by_window: {window: [d, ...]} of complete-block differences for one contrast.
    direction: +1 when the claim is 'effect > 0' (an advantage), -1 when it is 'effect < 0' (harm).
    Returns the estimate, the primary Hoeffding bound, the decisions, and the secondary summaries."""
    windows = sorted(diffs_by_window)
    all_d = [x for w in windows for x in diffs_by_window[w]]
    B = len(all_d)
    if B == 0:
        return {"n_blocks": 0}
    per_w = {w: (sum(v) / len(v) if v else float("nan")) for w, v in diffs_by_window.items()}
    # window-averaged estimate over the windows that hold data; the bound carries the same weights
    used = [w for w in windows if diffs_by_window[w]]
    est = sum(per_w[w] for w in used) / len(used)
    h = weighted_hoeffding_halfwidth([len(diffs_by_window[w]) for w in used], alpha)
    bound = est - h if direction > 0 else est + h        # lower bound for advantages, upper for harm
    missing_w = sorted(set(planned_windows or []) - set(used))
    out = {"n_blocks": B, "estimate": est, "primary_bound": bound, "halfwidth": h,
           "windows_with_data": len(used), "windows_missing": missing_w,
           "by_window": {w: {"estimate": per_w[w], "n_blocks": len(diffs_by_window[w]),
                             "hoeffding_95": hoeffding_halfwidth(len(diffs_by_window[w]), 0.05)}
                         for w in windows}}
    if direction > 0:
        out["verified"] = bound > 0
    else:
        out["verified_any_harm"] = bound < 0
        if margin is not None:
            out["verified_margin"] = bound <= -margin
    # secondary: stratified normal with the conservative blocked-design variance
    var = 0.0
    for w in used:
        v = diffs_by_window[w]
        if len(v) > 1:
            m = sum(v) / len(v)
            var += sum((x - m) ** 2 for x in v) / (len(v) - 1) / len(v)
    var /= len(used) ** 2
    z = normal_quantile(1 - alpha)
    out["secondary_normal_bound"] = est - z * math.sqrt(var) if direction > 0 else est + z * math.sqrt(var)
    return out


def heterogeneity(diffs_by_window):
    """Pearson chi-square on the window x {-1, 0, 1} table of block differences. Descriptive only:
    a non-significant result does not show that the effect was stable."""
    windows = [w for w in sorted(diffs_by_window) if diffs_by_window[w]]
    cats = (-1, 0, 1)
    table = [[sum(1 for x in diffs_by_window[w] if x == c) for c in cats] for w in windows]
    col = [sum(r[j] for r in table) for j in range(3)]
    cols = [j for j in range(3) if col[j] > 0]
    total = sum(col)
    if len(windows) < 2 or len(cols) < 2 or total == 0:
        return {"chi2": 0.0, "df": 0, "p_value": 1.0}
    chi2 = 0.0
    for r in table:
        rs = sum(r)
        for j in cols:
            e = rs * col[j] / total
            if e > 0:
                chi2 += (r[j] - e) ** 2 / e
    df = (len(windows) - 1) * (len(cols) - 1)
    return {"chi2": chi2, "df": df, "p_value": chi2_sf(chi2, df)}


def chi2_sf(x, k):
    """Survival function of the chi-square distribution via the regularized upper gamma function."""
    if x <= 0:
        return 1.0
    return _gammaincc(k / 2.0, x / 2.0)


def _gammaincc(a, x):
    if x < a + 1:  # series for the lower function
        term = s = 1.0 / a
        n = a
        for _ in range(500):
            n += 1
            term *= x / n
            s += term
            if abs(term) < abs(s) * 1e-12:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    # continued fraction for the upper function
    b, c, d = x + 1 - a, 1.0 / 1e-300, 1.0 / (x + 1 - a)
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-12:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def pooled_cp(k_a, n_a, k_b, n_b, alpha, direction):
    """Comparability column: the original construction on pooled counts (alpha split over the two
    endpoints). Valid only if each condition's draws form one binomial sample."""
    if clopper_pearson is None or not n_a or not n_b:
        return None
    if direction > 0:
        return clopper_pearson(k_a, n_a, alpha)[0] - clopper_pearson(k_b, n_b, alpha)[1]
    return clopper_pearson(k_a, n_a, alpha)[1] - clopper_pearson(k_b, n_b, alpha)[0]
