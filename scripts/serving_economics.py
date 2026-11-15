#!/usr/bin/env python3
"""Chapter 20 arithmetic (no API). All volumes, hourly prices and throughputs are ASSUMED and labelled in the text."""
from costlab.serving import *
print("== batch share (ASSUMED monthly synchronous spend $40,000, batch factor 0.5 from the vendor page)")
for share in (0.05, 0.10, 0.30, 0.50):
    c = batch_cost(40000, share)
    print(f"batchable share {share:4.0%}: blended ${c:,.0f}  saving ${40000-c:,.0f} ({1-c/40000:.1%})")
print("\n== self-hosting, ASSUMED: one GPU at $3.49/hour sustaining 1,000 output tokens/s at the latency target; API $3.50 per million output tokens")
H, TH, API = 3.49, 1000, 3.50
print(f"tokens/hour to match the API price: {breakeven_tokens_per_hour(H, API)/1e6:.2f} million")
print(f"U* (break-even utilisation) = {breakeven_utilisation(H, TH, API):.3f}")
for u in (1.0, 0.5, 0.25, 0.10, 0.05):
    print(f"utilisation {u:4.0%}: ${effective_self_host_per_mtok(H, TH, u):6.2f} per million output tokens  ({1/u:4.0f}x the full-use figure)")
print("\n== capacity for a peak (ASSUMED peak 3,500 tokens/s, one unit 1,000 tokens/s, run at 70% at peak)")
n = units_needed(3500, 1000)
cost = committed_capacity_cost(n, H)
print(f"units {n}, monthly ${cost:,.0f}")
avg_tps = 600
print(f"if average demand is {avg_tps} tokens/s the fleet's average utilisation is {avg_tps/(n*1000):.1%}, effective ${effective_self_host_per_mtok(H*n, n*1000, avg_tps/(n*1000)):.2f} per million output tokens")
