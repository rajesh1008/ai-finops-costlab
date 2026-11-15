#!/usr/bin/env python3
"""Chapter 16 arithmetic (no API). Break-even for replacing a model call with a rule path. Rates come from costlab.prices (placeholder table)
and all volumes, hit rates and engineering costs are ASSUMED."""
from costlab.estimate import estimate_usd
M = "anthropic:claude-haiku-4-5-20251001"
print("per-call cost at placeholder rates, 4 output tokens:")
for tin in (45, 600, 3000, 12000):
    print(f"  input {tin:>6} tokens: ${estimate_usd(M, tin, 4, 0, 0):.6f}")
print("\nmonths to repay a one-off $4,000 rule build plus $300 a month upkeep (ASSUMED), rules catch 64% of traffic")
print(f"{'input tokens':>12} {'tickets/month':>14} {'saving/month':>13} {'net/month':>10} {'months to repay':>16}")
for tin in (45, 3000, 12000):
    for vol in (100_000, 1_000_000, 10_000_000):
        s = estimate_usd(M, tin, 4, 0, 0) * vol * 0.64
        net = s - 300
        print(f"{tin:>12} {vol:>14,} {s:>13,.0f} {net:>10,.0f} {('never' if net <= 0 else f'{4000/net:.1f}'):>16}")
