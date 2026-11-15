"""Chapter 48: a canary battery for the facts a cost model leans on. Each check is a pure function over recorded observations, so the harness can be tested without a network."""
def count_matches_usage(count_in, usage_in, tol=0): return abs(count_in - usage_in) <= tol
def counts_deterministic(a, b): return a == b
def cost_identity(tin, tout, usd_in, usd_out, billed, tol=1e-9): return abs(tin / 1e6 * usd_in + tout / 1e6 * usd_out - billed) <= tol
def cache_expected(prefix_tokens, minimum, cache_read_tokens):
    """True when behaviour matches the documented minimum: below it nothing is read, at or above it the second call reads the prefix."""
    return (cache_read_tokens == 0) if prefix_tokens < minimum else (cache_read_tokens > 0)
def summarise(rows):
    out = {}
    for r in rows: out.setdefault(r["check"], []).append(r["ok"])
    return {k: (sum(v), len(v)) for k, v in out.items()}
