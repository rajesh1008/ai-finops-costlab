"""Chapter 22: restart models and loop signals. CCRM formulas follow arXiv 2605.08563 (opened 10 Nov 2026). Lab inputs are SYNTHETIC."""
import math, random

def ccrm_success(p0, p1, k):
    """P(success within k attempts): first attempt p0, every attempt after a failure p1 (contaminated)."""
    return p0 + (1 - p0) * (1 - (1 - p1) ** (k - 1)) if k >= 1 else 0.0

def clean_success(p0, k):
    return 1 - (1 - p0) ** k

def fit_p1(p0, pass_k, k):
    """Invert ccrm_success for p1 given p0 and measured pass@k."""
    return 1 - (1 - (pass_k - p0) / (1 - p0)) ** (1 / (k - 1))

def expected_attempts(p0, p1, k):
    """Expected number of attempts used when you stop at first success or at k."""
    e, alive = 0.0, 1.0
    for i in range(1, k + 1):
        e += alive
        alive *= (1 - (p0 if i == 1 else p1))
    return e

def cost_per_success(p0, p1, k, cost_first, cost_retry):
    """Expected spend divided by success probability, with attempt 1 costing cost_first and each retry cost_retry."""
    e_retries = expected_attempts(p0, p1, k) - 1
    return (cost_first + e_retries * cost_retry) / ccrm_success(p0, p1, k)

def simulate(p0, p1, k, n=20000, seed=5):
    rnd = random.Random(seed); ok = 0
    for _ in range(n):
        for i in range(k):
            if rnd.random() < (p0 if i == 0 else p1): ok += 1; break
    return ok / n

def loop_signals(actions):
    """actions: list of normalised action signatures. Returns repeat_run (longest run of identical), abab (an A,B,A,B window exists), distinct_share."""
    best = run = 1 if actions else 0
    for a, b in zip(actions, actions[1:]):
        run = run + 1 if a == b else 1; best = max(best, run)
    abab = any(actions[i] == actions[i + 2] and actions[i + 1] == actions[i + 3] and actions[i] != actions[i + 1] for i in range(len(actions) - 3))
    return {"repeat_run": best, "abab": abab, "distinct_share": len(set(actions)) / len(actions) if actions else 0.0}
