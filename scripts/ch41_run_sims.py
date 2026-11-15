#!/usr/bin/env python3
"""Offline arithmetic behind the 41st-run sections (Ch10-12, 30, 33-36, 40-42, 44-46, 48). All inputs invented and labelled in the chapters. Seeded; no API."""
import math, random
def cdf(z): return 0.5 * (1 + math.erf(z / math.sqrt(2)))
def run():
    out = {}
    # Ch30 commitment with discount
    d = 0.15; commit = 600_000; sc = [(450_000, .15), (550_000, .20), (700_000, .30), (900_000, .25), (1_100_000, .10)]
    rows = []
    for L, p in sc:
        c = max(commit, (1 - d) * L); rows.append((L, p, c, L - c))
    out["ch30"] = {"breakeven_list": commit / (1 - d), "rows": rows, "ev_saving": sum(p * s for _, p, _, s in rows)}
    # Ch33 lognormal usage
    r = random.Random(41); u = sorted(r.lognormvariate(math.log(40), 0.9) for _ in range(10_000)); lim = u[int(.95 * 10_000)]
    out["ch33"] = {"median": u[5000], "mean": sum(u) / len(u), "limit_p95": lim, "within80_100": sum(1 for x in u if .8 * lim <= x < lim), "over": sum(1 for x in u if x >= lim),
                   "cap_removed_share": sum(max(0, x - lim) for x in u) / sum(u), "over_p90_share": sum(max(0, x - u[9000]) for x in u) / sum(u), "limit_p90": u[9000], "within80_100_p90": sum(1 for x in u if .8 * u[9000] <= x < u[9000]), "over_p90": sum(1 for x in u if x >= u[9000])}
    # Ch34
    out["ch34"] = {(n, p): 1 - (1 - p) ** n for n in (25, 60, 100) for p in (.02, .05)}; out["ch34"]["n95_at_2pct"] = math.log(.05) / math.log(.98)
    # Ch35
    out["ch35"] = {"breakeven_reg": 400 / (40_000 * 0.90), "net_at_1_5pct": 400 - 40_000 * .015 * .90}
    # Ch36
    shared = 30_000; tok = (60, 30, 10); req = (20, 30, 50); eq = (1/3,) * 3
    out["ch36"] = {"tokens": [shared * x / 100 for x in tok], "requests": [shared * x / 100 for x in req], "equal": [shared * x for x in eq]}
    # Ch40 price/volume/mix
    # month A: model X 1.0B tokens at $3, model Y 0.5B at $10 per M blended; month B
    A = {"X": (1000, 3.0), "Y": (500, 10.0)}; B = {"X": (900, 3.0), "Y": (850, 10.0)}  # millions of tokens, $/M
    costA = sum(q * p for q, p in A.values()); costB = sum(q * p for q, p in B.values())
    out["ch40"] = {"A": costA, "B": costB, "delta": costB - costA}
    # Ch41
    out["ch41"] = {"cost": 14 * 2400, "saving_month": 90_000 * .06, "payback": 14 * 2400 / (90_000 * .06)}
    # Ch42 coverage
    w = []
    cov = [.55, .60, .66, .72, .77, .82, .86, .89, .92, .94, .95, .96]; spend = 50_000
    out["ch42"] = {"unalloc_total": sum(spend * (1 - c) for c in cov), "wk12": spend * (1 - cov[-1]), "wk1": spend * (1 - cov[0])}
    # Ch44
    out["ch44"] = {"rate_hr": 4180 / 6.5, "per_min": 4180 / 6.5 / 60, "if_detected_at_40min": 4180 / 6.5 * (40 / 60)}
    # Ch45 accrual
    out["ch45"] = {"meter": 212_400, "accr_low": 212_400 * 1.015, "accr_mid": 212_400 * 1.023, "accr_high": 212_400 * 1.031}
    # Ch46
    s = 100_000 * (1 - .91 * .86 * .94); out["ch46"] = {"claimed": 29_000, "actual": s, "over": 29_000 - s, "pct": (29_000 - s) / s}
    # Ch48
    out["ch48"] = {n: (f, pc, f / pc, f / pc * 2) for n, f, pc in [("cache layer", 6000, .08), ("router", 15000, .12), ("distilled model", 30000, .20), ("fine-tune pipeline", 22000, .10)]}
    # Ch10 thresholds
    cv = .12; out["ch10"] = {t: (1 - cdf(t / cv), 1 - cdf((t - .25) / cv)) for t in (.2, .3, .4)}
    # Ch11 cohort maturation: outcomes arrive with geometric lag, 40% outcome rate, 30% of eventual outcomes recorded per week-ish
    spend = 5000; recs = [1 - .6 ** k for k in range(1, 6)]
    out["ch11"] = {k + 1: (spend * 7 / (.4 * 1000 * 7 * recs[k] / 1)) for k in range(5)}
    # Ch12 free tier
    out["ch12"] = {"cost_per_conv": .35 * 4 / .03, "payback_months": (.35 * 4 / .03) / (24 * .70)}
    return out
if __name__ == "__main__":
    import pprint; pprint.pprint(run(), width=140)
