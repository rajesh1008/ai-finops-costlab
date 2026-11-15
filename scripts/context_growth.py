#!/usr/bin/env python3
"""Chapter 7: why step count is not linear in cost. ASSUMED: floor 613 (lab), each step appends 300 tokens
(tool result plus reply), output 80 tokens a step, placeholder rates $1 in / $5 out per million, no caching.
Then the same with cached history read at 0.1x and a write premium of 1.25x on each new 300 tokens."""
FLOOR, ADD, OUT = 613, 300, 80
IN, OUTR, READ, WRITE = 1.0, 5.0, 0.1, 1.25
def cost(steps, cached):
    tot = 0.0
    hist = 0
    for i in range(steps):
        if cached:
            tot += (FLOOR + hist) / 1e6 * READ + (ADD if i else 0) / 1e6 * WRITE
        else:
            tot += (FLOOR + hist) / 1e6 * IN
        tot += OUT / 1e6 * OUTR
        hist += ADD
    return tot
print(f"{'steps':>6s} {'no cache':>10s} {'cached':>10s} {'per-step x vs 1 step (no cache)':>32s}")
base = cost(1, False)
for n in (1, 2, 4, 8, 20, 50, 163):
    c, k = cost(n, False), cost(n, True)
    print(f"{n:>6d} {c:>10.4f} {k:>10.4f} {c/base:>25.1f}x total, {c/n/base:.1f}x per step")
