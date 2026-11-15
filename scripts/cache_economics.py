#!/usr/bin/env python3
"""Chapter 18 arithmetic (no API). Multipliers from the vendor page opened 10 Nov 2026; volumes ASSUMED."""
from costlab.cachelab import *
print("break-even reads: 5-minute write", breakeven_reads(W5), " 1-hour write", breakeven_reads(W1H))
P = 1.00  # Haiku 4.5 input USD per million tokens (vendor page)
print("\n20k-token prefix, 300-token suffix, Haiku 4.5 rates")
for mode in ("none", "write5", "write1h", "read"):
    print(f"  {mode:8s} ${call_cost(20000, 300, P, mode):.5f}")
print("\nTen calls, gap in minutes between calls, 20k prefix (cost of the ten calls)")
print("gap  no-cache   5m-cache  (writes/reads)   1h-cache (writes/reads)")
for gap in (1, 3, 4.9, 5.1, 8, 20, 50, 70):
    g = [gap] * 9
    nc = 10 * call_cost(20000, 300, P, "none")
    c5, w5, r5 = session_cost(g, 20000, 300, P, 5, W5)
    c1, w1, r1 = session_cost(g, 20000, 300, P, 60, W1H)
    print(f"{gap:4}  ${nc:.4f}   ${c5:.4f}  ({w5}/{r5})      ${c1:.4f}  ({w1}/{r1})")
print("\nKeepalive paper formulas: I_max = tau*(w/r-1)")
for name, tau, w in (("5-minute tier, tau=4", 4, 1.25), ("1-hour tier, tau=50", 50, 2.0)):
    print(f"  {name}: I_max = {keepalive_i_max(tau, w):.1f} min")
print("\nHolding a 100k prefix 60 minutes at tau=4: ", f"{keepalive_cost_per_token(60, 4):.2f} x input price per token vs re-write {W5}")
