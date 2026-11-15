#!/usr/bin/env python3
"""Chapter 12 follow-up (nineteenth run), OFFLINE SIMULATION on the Chapter 12 synthetic customers (seed 12, 400 customers, every parameter ASSUMED except the multiplier).
A runaway task costs `mult` times a normal task. The multiplier 46 is taken from the Chapter 44 labs: a 30-step runaway on claude-haiku-4-5 cost $0.0921 against about $0.0020 for the 2-step normal
run of the same agent at placeholder rates (ratio 46). A fraction f of tasks is a runaway (seed 12 draw per task, assigned per customer in proportion to tasks). A per-task cap limits the cost of any task to cap_mult times a normal task.
Three price models as in Chapter 12. Reports gross margin and negative-margin customer share. Output runs/margin-runaway-sim-2026-11-11.txt."""
import random
from pathlib import Path
from costlab.margin import customers, seat_price, seat_with_allowance, per_task
MODELS = {"flat seat $50": seat_price, "seat $50 + 50 tasks/seat, $1.20 over": seat_with_allowance, "per task $1.50": per_task}
def run(f, mult, cap_mult=None, seed=12):
    rnd = random.Random(seed); cs = customers(); res = {}
    for name, fn in MODELS.items():
        rev = cost = 0.0; neg = 0
        for c in cs:
            normal = c.tasks * c.cost_per_task
            n_run = sum(1 for _ in range(c.tasks) if rnd.random() < f) if f > 0 else 0
            m = mult if cap_mult is None else min(mult, cap_mult)
            k = normal + n_run * c.cost_per_task * (m - 1)
            r = fn(c); rev += r; cost += k; neg += (r - k) < 0
        res[name] = (1 - cost / rev, neg / len(cs))
    return res
lines = ["Chapter 12 customers, runaway multiplier 46 (from the Chapter 44 labs), cap = 5x a normal task where stated"]
for f in (0.0, 0.001, 0.005, 0.01):
    for cap in (None, 5):
        r = run(f, 46, cap); lines.append(f"runaway share {f*100:.1f}% of tasks, {'no cap' if cap is None else 'cap 5x'}: " + " | ".join(f"{k}: margin {v[0]*100:.1f}% neg {v[1]*100:.1f}%" for k, v in r.items()))
(Path(__file__).resolve().parents[1] / "runs" / "margin-runaway-sim-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
