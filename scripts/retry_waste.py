#!/usr/bin/env python3
"""Chapter 7: retry waste, tool registry overhead, human wait. SYNTHETIC and ASSUMED inputs; arithmetic only, no API."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.waste import simulate_retries, tool_overhead, human_wait_cost

print("A. Retry waste (SYNTHETIC: 5,000 tasks, one call each, 6,000 input and 400 output tokens, seed 11)")
print(" p_fail cap correlated outcomes calls  waste_share  cost_per_outcome")
for p, cap, cor in [(0.05,1,0),(0.05,3,0),(0.05,3,0.9),(0.20,3,0),(0.20,3,0.9),(0.20,6,0.9),(0.20,1,0)]:
    r = simulate_retries(p, cap, correlated=cor)
    print(f" {p:5.2f} {cap:3d} {cor:9.1f} {r.outcomes:8d} {r.calls:5d}  {r.waste_share:10.1%}  ${r.total_cost/max(r.outcomes,1):.5f}")

print("\nB. Tool registry overhead per session (ASSUMED 120 tokens per tool description; fixed 496 from vendor page)")
print(" tools steps  per_step  session_tokens  uncached_usd  cached_usd")
for n, steps in [(5,10),(5,40),(40,10),(40,40),(128,10),(128,40)]:
    t = tool_overhead(n, 120, steps)
    print(f" {n:5d} {steps:5d} {t['per_step']:9d} {t['session_tokens']:15d}  {t['usd_uncached']:11.4f}  {t['usd_cached']:10.4f}")

print("\nC. Human in the loop (ASSUMED cache lifetime 5 minutes; 20,000-token prefix; 150 output tokens per turn)")
cases = {"quick approvals (1,2,1,3 min)":[1,2,1,3], "one lunch (1,2,45,3)":[1,2,45,3],
         "slow reviewer (8,12,9,15)":[8,12,9,15], "ten minutes each, twelve turns":[10]*12}
for name, w in cases.items():
    h = human_wait_cost(20000, w)
    print(f" {name:36s} calls {h['calls']:2d} expired {h['expired']:2d} cost ${h['cost']:.4f} if cache never expired ${h['if_never_expired']:.4f} ratio {h['cost']/h['if_never_expired']:.2f}")
