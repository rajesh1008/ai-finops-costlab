#!/usr/bin/env python3
"""Chapter 14: what a published price-decline rate is worth to one product, net of the cost of moving. ARITHMETIC on stated assumptions. No API.

The decline rates are Epoch AI's published frontier averages (47% a quarter average; 66% at state-of-the-art debut and 32% two years later).
Epoch warns that real users do not sit on the frontier. `captured` is the share of the published decline this product is assumed to realise.
"""
import itertools

def run(monthly_spend0, decline_q, captured, switch_every_q, switch_cost, quarters=8):
    spend = 0.0; cost_now = monthly_spend0; moves = 0
    for q in range(1, quarters + 1):
        spend += 3 * cost_now
        if q % switch_every_q == 0:
            cost_now *= (1 - decline_q * captured) ** switch_every_q
            spend += switch_cost; moves += 1
    return spend, moves

base = 40_000  # USD a month, SYNTHETIC
print(f"SYNTHETIC product spending ${base:,} a month at the start; 8 quarters; each migration costs a stated one-off (evals + engineering + shadow run).")
print("policy A: never move (cost per month flat at list). policy B/C: move every 2 or 4 quarters.")
flat, _ = run(base, 0.0, 1.0, 99, 0)
print(f"A  never move: ${flat:,.0f} over 8 quarters\n")
print("declines per quarter     captured  switch every  one-off cost   total        vs A")
for dq, cap, k, sc in itertools.product((0.32, 0.47), (0.2, 0.5), (2, 4), (25_000, 80_000)):
    tot, moves = run(base, dq, cap, k, sc)
    print(f"{dq:5.0%}                  {cap:7.0%}   {k:8d} q   ${sc:9,}   ${tot:11,.0f}  {tot/flat-1:+7.1%}")
print("\nBreak-even monthly spend for one move (32% a quarter, 50% captured, one move after 2 quarters, 6 quarters of benefit afterwards):")
for sc in (25_000, 80_000):
    f = (1 - 0.32 * 0.5) ** 2
    saving_per_month_per_dollar = 1 - f
    be = sc / (18 * saving_per_month_per_dollar)
    print(f"  one-off ${sc:,}: break-even at about ${be:,.0f} a month of spend")
