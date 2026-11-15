#!/usr/bin/env python3
"""Chapter 15 lab. SYNTHETIC. Three tables: (1) buyer's price per truly resolved conversation when the billing
rule counts 'assumed' resolutions, (2) break-even resolution rate for a vendor, (3) twelve months of vendor margin
under seat, outcome and hybrid prices when the resolution rate wobbles."""
import random, statistics
from costlab.pricing import *

print("TABLE 1: buyer price per TRUE resolution (list price $0.99 per billed outcome; n=20000, seed 15)")
print(f"{'true rate':>10} {'assumed-leak':>13} {'recontact':>10} {'billed':>7} {'true':>6} {'deducted':>9} {'$/true':>8}")
for p_true in (0.45, 0.60):
    for q, rc in ((0.0, 0.0), (0.15, 0.0), (0.15, 0.4), (0.30, 0.4)):
        r = billed_outcomes(20000, p_true, q, rc, random.Random(15))
        print(f"{p_true:>10.2f} {q:>13.2f} {rc:>10.2f} {r['billed']:>7} {r['true']:>6} {r['deducted']:>9} {buyer_price_per_true(0.99, r):>8.3f}")

print("\nTABLE 2: break-even resolution rate = cost per conversation / price per outcome")
prices = (0.99, 1.50, 2.00)
print(f"{'cost/conv':>10} " + " ".join(f"{'$%.2f' % p:>8}" for p in prices))
for c in (0.10, 0.25, 0.40, 0.60, 1.00):
    cells = []
    for p in prices:
        b = breakeven_resolution_rate(c, p)
        cells.append(f"{b:>8.0%}" if b <= 1 else f"{'never':>8}")
    print(f"{c:>10.2f} " + " ".join(cells))

print("\nTABLE 3: vendor gross margin by month, n=10,000 conversations, cost $0.31 per conversation")
for label, drift in (("steady", 0.0), ("model change drops resolution 1.2 pts a month", -0.012)):
    rows = six_month_variance(drift=drift)
    print(f"-- {label}")
    print(f"{'month':>5} {'res rate':>9} {'seat $6k':>9} {'outcome':>9} {'hybrid':>9}")
    for m, rr, a, b, c in rows:
        print(f"{m:>5} {rr:>9.1%} {a:>9.1%} {b:>9.1%} {c:>9.1%}")
    for name, i in (("seat", 2), ("outcome", 3), ("hybrid", 4)):
        v = [r[i] for r in rows]
        print(f"  {name:8} mean {statistics.mean(v):.1%}  stdev {statistics.pstdev(v):.1%}  min {min(v):.1%}")
