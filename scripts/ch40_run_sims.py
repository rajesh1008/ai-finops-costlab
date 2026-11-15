#!/usr/bin/env python3
"""40th run offline seeded sims (no API calls). Illustrative inputs, all invented. Prints figures used in Ch5, Ch8, Ch15, Ch16, Ch20, Ch30."""
import random, math, statistics as st
def ch5_sampling(seed=5):
    r = random.Random(seed); n = 200_000
    cost = [r.lognormvariate(math.log(0.02), 1.4) for _ in range(n)]
    for i in r.sample(range(n), 40): cost[i] *= 400            # forty runaway sessions
    tot = sum(cost); out = {"n": n, "total": tot, "runaway_share": sum(sorted(cost)[-40:]) / tot}
    for rate in (0.01, 0.05):
        errs = []
        for t in range(300):
            rr = random.Random(t * 31 + int(rate * 1000)); s = [c for c in cost if rr.random() < rate]
            errs.append(abs(sum(s) / rate - tot) / tot)
        errs.sort(); out[rate] = (st.mean(errs), errs[int(.95 * len(errs))])
    return out
def ch8_volume():
    calls = 5_000_000; res = {}
    for kb in (1.2, 4.0): res[kb] = (calls * kb / 1e6, calls * kb / 1e6 * 30)    # GB/day, GB/month
    return res
def ch15_outcome_price(c=0.60):
    return {s: (c / s, 4.0 - c / s, (4.0 - c / s) / 4.0) for s in (0.6, 0.7, 0.8, 0.9)}
def ch16_review(a=0.40, h=2.50, r=12.0):
    # autonomous cost a per task; error e costs r (rework or refund). Human review costs h, catches 90 percent of errors.
    be = h / (0.9 * r); return {"breakeven_error_rate": be, "review_cost_at_e": {e: (a + h + e * 0.1 * r, a + e * r) for e in (0.05, 0.1, 0.2, 0.3)}}
def ch20_batch(price=1.0, disc=0.5):
    out = {}
    for f, miss in ((0.3, 0.02), (0.6, 0.02), (0.6, 0.10), (0.8, 0.10)):
        eligible = 1 - f; cost = f * price + eligible * ((1 - miss) * price * (1 - disc) + miss * (price * (1 - disc) + price))
        out[(f, miss)] = (cost, 1 - cost)
    return out
def ch30_commit(sigma=0.25, disc=0.20, seed=30, trials=20000):
    r = random.Random(seed); res = {}
    spends = [100 * math.exp(r.gauss(-sigma ** 2 / 2, sigma)) for _ in range(trials)]
    for pct in (0.6, 0.8, 0.9, 1.0, 1.1):
        C = 100 * pct; costs = []
        for s in spends: costs.append(C * (1 - disc) + max(0, s - C))
        res[pct] = (st.mean(costs), sum(1 for s in spends if s < C) / trials)
    res["on_demand"] = st.mean(spends); return res
if __name__ == "__main__":
    for f in (ch5_sampling, ch8_volume, ch15_outcome_price, ch16_review, ch20_batch, ch30_commit): print(f.__name__, f())
