#!/usr/bin/env python3
"""Chapter 18 lab (no API). SYNTHETIC question pairs (seed 18) and a character-trigram cosine as a stand-in for an embedding.
This is not a neural encoder; the point is the shape of the threshold trade-off and the cost arithmetic, not a model ranking."""
from costlab.cachelab import *
pairs = make_pairs()
print("pairs", len(pairs), " same-answer", sum(1 for p in pairs if p[2]), " different-answer", sum(1 for p in pairs if not p[2]))
rows = sweep(pairs, [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
print("thr   hit_rate  false_hits  false_share_of_hits  safe_hit_rate")
for r in rows:
    print(f"{r['threshold']:.2f}  {r['hit_rate']:.3f}     {r['false_hits']:3d}        {r['false_hit_share_of_hits']:.3f}                {r['safe_hit_rate']:.3f}")
CALL = 0.0006  # ASSUMED USD per answered call
for pen in (0.0, 0.01, 0.50, 5.00):
    best = min(rows, key=lambda r: expected_cost_per_query(r, CALL, pen))
    print(f"\npenalty ${pen:.2f} per false hit: expected cost per query by threshold")
    print("  " + "  ".join(f"{r['threshold']:.2f}:${expected_cost_per_query(r, CALL, pen):.5f}" for r in rows))
    print(f"  no cache: ${CALL:.5f}   best threshold {best['threshold']:.2f}")
print("\nexample false hit above 0.80 (same question, other account):")
for a, b, same in pairs:
    if not same and cosine(trigrams(a), trigrams(b)) >= 0.90:
        print("  ", a, "|", b, f"cos={cosine(trigrams(a), trigrams(b)):.3f}"); break
