"""Stop-reason and output-multiple helpers (twenty-first run). Pure functions over cost records (dicts), used by Ch8, Ch9, Ch22 and Ch26.
A record needs: model, kind (optional), out (billed output tokens), stop (stop reason). Nothing here calls an API."""
from collections import defaultdict

def truncation_share(records, by="model"):
    """Share of calls and share of billed output tokens that ended at the ceiling (stop == 'max_tokens'), grouped by a field."""
    g = defaultdict(lambda: [0, 0, 0, 0])
    for r in records:
        a = g[r.get(by)]; a[0] += 1; a[1] += r["out"]
        if r["stop"] == "max_tokens": a[2] += 1; a[3] += r["out"]
    return {k: {"calls": v[0], "truncated_calls": v[2], "call_share": v[2] / v[0], "token_share": (v[3] / v[1]) if v[1] else 0.0} for k, v in g.items()}

def output_multiple(records, base_model, by="kind"):
    """Mean billed output per call for each model by kind, as a multiple of base_model's mean for the same kind."""
    s = defaultdict(lambda: [0, 0])
    for r in records:
        a = s[(r["model"], r.get(by))]; a[0] += r["out"]; a[1] += 1
    mean = {k: v[0] / v[1] for k, v in s.items()}
    out = {}
    for (m, k), v in mean.items():
        b = mean.get((base_model, k))
        if b: out[(m, k)] = v / b
    return out

def cost_per_correct(records, p_in, p_out):
    """Dollars per correct verdict: total cost over number of records with right True. Prices per million tokens."""
    cost = sum(r["in"] * p_in + r["out"] * p_out for r in records) / 1e6
    ok = sum(1 for r in records if r.get("right"))
    return cost / ok if ok else float("inf")
