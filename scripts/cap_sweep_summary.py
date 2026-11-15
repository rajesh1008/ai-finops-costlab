#!/usr/bin/env python3
"""Chapter 26 cap sweep: arithmetic over cap-sweep-lab and budget-policy-lab JSON. No API. Caps 0.003, 0.006, 0.020 from the sweep; 0.012 and the uncapped arm from the original lab (different sampling draws)."""
import json
from pathlib import Path
from costlab.agentrun import run_cost
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
from costlab.ladder import wilson
R = Path(__file__).resolve().parents[1] / "runs"; p = P["anthropic:claude-haiku-4-5-20251001"]
def load(f): 
    d = [r for r in json.load(open(R / f))["results"] if r["status"] != "api_error"]
    for r in d: r["cost"] = run_cost(r["steps"], p["input"], p["output"])
    return d
a = load("budget-policy-lab-2026-11-10.json"); s = load("cap-sweep-lab-2026-11-10.json")
groups = [("none", [r for r in a if r["policy"] == "none"])] + [(f"{c:.3f}", [r for r in s if r["cap"] == c]) for c in (0.003, 0.006)] + [("0.012", [r for r in a if r["policy"] == "hard"]), ("0.020", [r for r in s if r["cap"] == 0.02])]
base = sum(r["cost"] for r in groups[0][1])
for name, g in groups:
    ok = sum(r["ok"] for r in g); lo, hi = wilson(ok, len(g)); tot = sum(r["cost"] for r in g)
    k = sum(r["status"] == "killed" for r in g)
    print(f"cap {name:6s}: runs {len(g)} correct {ok} = {ok/len(g):.3f} (95% {lo:.2f}-{hi:.2f}) spend ${tot:.3f} ({tot/base:.2f}x of none) killed {k} cost per correct ${tot/max(ok,1):.5f}")
for h in (3, 5):
    print(f"  {h} hops correct:", ", ".join(f"{n} {sum(r['ok'] for r in g if r['n_pairs']==h)}/{sum(1 for r in g if r['n_pairs']==h)}" for n, g in groups))
