#!/usr/bin/env python3
"""Chapter 42 summary: reads runs/firstmeter-lab-2026-11-11.json, prints accuracy, spend-weighted misattribution, unknown share, confusion, classifier cost, plus composed arithmetic."""
import json
from pathlib import Path
from costlab.firstmeter import parse_label, score, confusion, coverage_trajectory, residual, first_honest_number, NAMES
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
d = json.loads((Path(__file__).resolve().parents[1] / "runs" / "firstmeter-lab-2026-11-11.json").read_text())
reqs = d["requests"]; PM = {"h45": "anthropic:claude-haiku-4-5-20251001", "h55": "anthropic:claude-haiku-5-5"}
PPT = 1e-6  # ASSUMED blended $ per token of the logged calls ($1 per million)
for m in ("h45", "h55"):
    for v in "SU":
        rs = [x for x in d["results"] if x["m"] == m and x["view"] == v]
        rows = [{"feature": reqs[x["i"]]["feature"], "label": parse_label(x["text"]), "tokens": reqs[x["i"]]["tokens"]} for x in rs]
        s = score(rows, PPT); p = P[PM[m]]
        cost = sum(x["in"] * p["input"] + x["out"] * p["output"] for x in rs) / 1e6
        print(f"{m} view {v}: n={s['n']} acc={s['accuracy']:.3f} wrong_share={s['wrong_share']:.3f} unknown_share={s['unknown_share']:.3f} misattributed=${s['misattributed']:.4f} of ${s['spend']:.4f} classifier_cost=${cost:.4f} errors={sum(1 for x in rs if x['error'])}")
        if v == "U":
            c = confusion(rows)
            for f in NAMES: print("   ", f, {l: c.get((f, l), 0) for l in NAMES + ["unknown", "unparsed"] if c.get((f, l), 0)})
print("coverage trajectory (ASSUMED):", coverage_trajectory())
print("residual (COMPOSED month 3): invoice 214000 vs gateway ledger 196000:", residual(214_000.0, 196_000.0))
print("first honest number (COMPOSED support assistant): spend incl. untagged 98200, tagged to it 52000, signed outcomes 18500:", first_honest_number(98_200.0, 52_000.0, 18_500))
calls = 46_200.0 / (0.4426 / 160); print(f"untagged $46,200 at lab mean ${0.4426/160:.5f} per call = {calls:,.0f} calls")
for m, c in (("h45 U", 0.0357 / 160), ("h55 U", 0.0044 / 160)): print(f"  classify all with {m}: ${calls * c:,.0f} at ${c:.7f} per call")
