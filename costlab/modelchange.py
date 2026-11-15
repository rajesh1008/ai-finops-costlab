"""Chapter 35: judging a model change by outcomes, not by the price line. Classify each call under a strict JSON contract, count good outcomes, find the failure cost at which a saving
disappears, and replay a canary gate over recorded outcomes. Outcome classes: unparsed (strict json.loads fails, including empty), decline (both fields null), wrong (values present, not the gold), correct."""
import json, math, random, re
from .prices import PLACEHOLDER_USD_PER_MTIOK

def strip_fences(t):
    """The shim: remove one leading and trailing markdown code fence, nothing else."""
    t = (t or "").strip()
    m = re.fullmatch(r"```[a-zA-Z]*\s*(.*?)\s*```", t, re.S)
    return m.group(1) if m else t

def classify(text, gold, answerable, shim=False):
    """Returns one of: unparsed, correct, wrong, correct_decline, wrong_decline. shim=True strips a code fence first (the incumbent's wrapper)."""
    t = strip_fences(text) if shim else (text or "").strip()
    try: o = json.loads(t)
    except Exception: return "unparsed"
    if not isinstance(o, dict): return "unparsed"
    ref, days = o.get("ref"), o.get("days")
    if ref is None and days is None: return "wrong_decline" if answerable else "correct_decline"
    vals = [str(ref), str(days)]
    return "correct" if all(g in vals for g in gold) else "wrong"

GOOD = {"correct", "correct_decline"}

def call_cost(model, inp, out):
    t = PLACEHOLDER_USD_PER_MTIOK["anthropic:" + model]
    return inp / 1e6 * t["input"] + out / 1e6 * t["output"]

def break_even_failure_cost(cost_a, fail_a, cost_b, fail_b):
    """Failure cost F such that cost_a + fail_a*F == cost_b + fail_b*F. None if the failure rates are equal or B fails less and is also cheaper."""
    if fail_b <= fail_a: return None
    return (cost_a - cost_b) / (fail_b - fail_a)

def binom_tail(n, k, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0: return 1.0
    lp, lq = math.log(p), math.log(1 - p); head = 0.0
    for i in range(0, min(k, n + 1)):
        head += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
    return max(0.0, 1.0 - head)

def critical_failures(n, p0, alpha):
    """Smallest k >= 2 with P(X >= k | n, p0) < alpha, or None if no k <= n qualifies."""
    for k in range(2, n + 1):
        if binom_tail(n, k, p0) < alpha: return k
    return None

def canary_detect(outcomes_bad, p0, alpha=0.01, max_n=2000, trials=2000, seed=0):
    """outcomes_bad: list of 0/1 failure flags recorded for the candidate. Draw requests with replacement; after each request test H0: failure rate <= p0 (one-sided exact binomial,
    needing at least two failures). Return the request count at which the first rejection occurs in each trial (max_n+1 if none), sorted."""
    crit = [None] + [critical_failures(n, p0, alpha) for n in range(1, max_n + 1)]
    rnd = random.Random(seed); out = []
    for _ in range(trials):
        k = 0; hit = max_n + 1
        for n in range(1, max_n + 1):
            k += outcomes_bad[rnd.randrange(len(outcomes_bad))]
            if crit[n] is not None and k >= crit[n]: hit = n; break
        out.append(hit)
    return sorted(out)
