#!/usr/bin/env python3
"""Chapter 14 offline simulation (no API calls). A firm sits at a given true percentile of a peer population of cost per outcome. It is compared with n peers drawn at random. How wide is the range of percentile ranks it would be told it has? Population: lognormal, sigma 0.6. Seed 14. All parameters invented."""
import random, math, statistics as st
r = random.Random(14)
def rank_range(true_pct, n, trials=20000, sig=0.6):
    z = st.NormalDist().inv_cdf(true_pct)          # firm's position in standard normal units
    firm = math.exp(sig * z)
    ranks = []
    for _ in range(trials):
        peers = [math.exp(r.gauss(0, sig)) for _ in range(n)]
        ranks.append(100.0 * sum(1 for p in peers if p < firm) / n)
    ranks.sort()
    return ranks[int(0.05 * trials)], ranks[int(0.5 * trials)], ranks[int(0.95 * trials)]
if __name__ == "__main__":
    for true_pct in (0.25, 0.50, 0.75):
        for n in (5, 10, 20, 50, 200):
            lo, md, hi = rank_range(true_pct, n)
            print("true percentile %2d  peers %3d  reported rank 5th %.0f median %.0f 95th %.0f  width %.0f" % (true_pct * 100, n, lo, md, hi, hi - lo))
