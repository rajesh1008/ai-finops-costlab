#!/usr/bin/env python3
"""Chapter 2: the cost of crossing a long-context threshold by a few hundred tokens.

ASSUMED RATES (not a vendor's rate card): threshold 200,000 prompt tokens; below it $3 in / $15 out
per million; above it $6 in / $22.50 out per million. A 600-token answer in every case.
"""
from costlab.tiers import tiered_cost
args = dict(threshold=200_000, low_in=3.0, low_out=15.0, high_in=6.0, high_out=22.5)
print(f"{'prompt tokens':>14s} {'whole-request':>14s} {'excess-only':>12s}")
for p in (150_000, 199_000, 200_000, 200_500, 260_000):
    w = tiered_cost(p, 600, whole_request=True, **args)
    e = tiered_cost(p, 600, whole_request=False, **args)
    print(f"{p:>14,d} {w:>14.4f} {e:>12.4f}")
a = tiered_cost(200_000, 600, whole_request=True, **args)
b = tiered_cost(200_500, 600, whole_request=True, **args)
print(f"\n500 more tokens under the whole-request reading: ${b - a:.4f} more, {b / a - 1:.0%}")
