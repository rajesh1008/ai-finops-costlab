#!/usr/bin/env python3
"""Chapter 13: split a forecast miss into users, tasks per user, cost per task and a residual (log decomposition). SYNTHETIC history. No API."""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.forecast import history

h = {r["m"]: r for r in history()}
def decomp(at, target, ug=0.07, tg=0.03):
    last = h[at]; k = target - at
    fu = last["users"] * (1 + ug) ** k; ft = last["tpu"] * (1 + tg) ** k; fc = last["cpt"]
    f = fu * ft * fc; a = h[target]
    parts = {"users": math.log(a["users"] / fu), "tasks per user": math.log(a["tpu"] / ft), "cost per task": math.log(a["cpt"] / fc)}
    resid = math.log(a["spend"] / f) - sum(parts.values())
    return f, a["spend"], parts, resid
print("SYNTHETIC. Forecast made at month `at` by holding cost per task flat and growing users 7% and tasks per user 3% a month.")
for at, tgt in ((8, 10), (11, 14), (14, 17)):
    f, a, parts, resid = decomp(at, tgt)
    print(f"\nmade at month {at}, target month {tgt}: forecast ${f:,.0f}, actual ${a:,.0f}, miss {(f-a)/f:+.1%} of forecast")
    for k, v in parts.items():
        print(f"   {k:15s} {v:+.3f} log points  ({math.exp(v)-1:+.1%})")
    print(f"   residual (noise) {resid:+.3f}")
