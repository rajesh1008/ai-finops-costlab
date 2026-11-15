#!/usr/bin/env python3
"""Chapter 12: margin by customer under flat seat, seat with allowance, and per-task pricing. SYNTHETIC. No API."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.margin import *

cs = customers()
print(f"SYNTHETIC: {len(cs)} customers, seed 12; median 40 tasks per seat per month, lognormal sigma 1.1; about $0.55 per task (an agent task, not a single call).")
print(f"seats {sum(c.seats for c in cs)}, tasks {sum(c.tasks for c in cs):,}, serving cost ${sum(cost(c) for c in cs):,.0f}")
models = {"flat seat $50": seat_price, "seat $50 + 50 tasks per seat, $1.20 over": seat_with_allowance, "per task $1.50": per_task}
print("\nmodel                                         revenue   gross margin  negative-margin customers  p10 margin  top-decile cost share  top-decile revenue share  loss $")
for name, fn in models.items():
    s = summary(cs, fn)
    print(f"{name:44s} {s['revenue']:9,.0f}  {s['gm']:10.1%}  {s['neg_share']:20.1%}  {s['p10_gm']:12.1%}  {s['top_decile_cost_share']:10.1%}  {s['top_decile_rev_share']:14.1%}  {s['loss_dollars']:9,.0f}")
print("\nSensitivity: cost per task drops 40 percent while median usage per seat doubles (flat seat price)")
cs2 = customers(median_tasks_per_seat=80, base_cost=0.55 * 0.6)
for name, fn in models.items():
    s = summary(cs2, fn)
    print(f"{name:44s} margin {s['gm']:6.1%}  negative-margin {s['neg_share']:5.1%}")
print("\nSame, with usage doubled and cost unchanged:")
cs3 = customers(median_tasks_per_seat=80)
for name, fn in models.items():
    s = summary(cs3, fn)
    print(f"{name:44s} margin {s['gm']:6.1%}  negative-margin {s['neg_share']:5.1%}")
