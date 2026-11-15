"""Chapter 39: a pull-request cost estimator and its checks. Estimates are per call, in dollars, from the dated placeholder price table."""
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P


def rates(model, discount=0.0):
    r = P["anthropic:" + model]
    return {k: v * (1 - discount) for k, v in r.items()}


def est_list(tokens_in, assumed_out, model, discount=0.0):
    """Naive estimate: every input token at the input rate, assumed output tokens at the output rate, no cache."""
    r = rates(model, discount)
    return (tokens_in * r["input"] + assumed_out * r["output"]) / 1e6


def est_cache_aware(prefix_tokens, suffix_tokens, assumed_out, model, calls_per_lifetime, discount=0.0, cache=True):
    """Cache-aware estimate: one write and (n-1) reads of the prefix spread over n calls, plus suffix and output."""
    r = rates(model, discount)
    n = max(1, calls_per_lifetime)
    if not cache:
        return ((prefix_tokens + suffix_tokens) * r["input"] + assumed_out * r["output"]) / 1e6
    prefix = (prefix_tokens * r["cache_write"] + (n - 1) * prefix_tokens * r["cache_read"]) / n
    return (prefix + suffix_tokens * r["input"] + assumed_out * r["output"]) / 1e6


def flag(est, baseline, rise=0.20):
    """A PR is flagged when the estimated cost per call rises by more than `rise` against the baseline."""
    return est > baseline * (1 + rise)


def error_pct(est, actual):
    return (est - actual) / actual * 100.0
