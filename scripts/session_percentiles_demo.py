#!/usr/bin/env python3
"""Chapter 7 demonstration (SYNTHETIC, no API calls). 1,000 invented session costs from a seeded lognormal; shows how mean, median, p90 and p99 differ and what share of spend the top 1 and 5 percent of sessions carry."""
import random, statistics as st, math
def sessions(n=1000, seed=7, mu=math.log(0.40), sigma=1.0):
    r = random.Random(seed); return sorted(r.lognormvariate(mu, sigma) for _ in range(n))
def pct(v, q): return v[min(len(v) - 1, int(q * len(v)))]
def report(v):
    tot = sum(v); k1 = int(len(v) * 0.99); k5 = int(len(v) * 0.95)
    return {"n": len(v), "mean": tot / len(v), "median": st.median(v), "p90": pct(v, .90), "p99": pct(v, .99), "max": v[-1], "total": tot,
            "top1_share": sum(v[k1:]) / tot, "top5_share": sum(v[k5:]) / tot}
if __name__ == "__main__":
    for k, x in report(sessions()).items(): print(k, round(x, 4))
