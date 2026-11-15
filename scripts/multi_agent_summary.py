#!/usr/bin/env python3
"""Chapter 25: arithmetic over the recorded multi-agent-lab JSON. No API. haiku-4-5 placeholder rates."""
import json
from pathlib import Path
from costlab.agentrun import quantile
from costlab.multiagent import role_costs, overhead_share
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
p = P["anthropic:claude-haiku-4-5-20251001"]; ui, uo = p["input"], p["output"]
d = json.load(open(Path(__file__).resolve().parents[1] / "runs" / "multi-agent-lab-2026-11-10.json"))["results"]
d = [r for r in d if r["status"] != "api_error"]
for r in d: r["rc"] = role_costs(r["roles"], ui, uo); r["cost"] = sum(r["rc"].values()); r["calls"] = sum(len(v) for v in r["roles"].values()); r["inp"] = sum(s["in"] for v in r["roles"].values() for s in v)
def line(label, g):
    if not g: return
    c = [r["cost"] for r in g]
    print(f"{label}: runs {len(g)} correct {sum(r['ok'] for r in g)/len(g):.3f} mean cost ${sum(c)/len(c):.5f} p90 ${quantile(c,.9):.5f} max ${max(c):.5f} mean calls {sum(r['calls'] for r in g)/len(g):.2f} mean input tokens {sum(r['inp'] for r in g)/len(g):.0f}")
for arm, name in (("S", "single agent"), ("M", "supervisor+workers")):
    line(name + " all", [r for r in d if r["arm"] == arm])
    for n in (2, 6): line(f"  {name}, {n} combinations", [r for r in d if r["arm"] == arm and r["n"] == n])
print("status M: " + ", ".join(f"{k}={sum(1 for r in d if r['arm']=='M' and r['status']==k)}" for k in sorted({r['status'] for r in d if r['arm']=='M'})))
for n in (2, 6):
    m = [r for r in d if r["arm"] == "M" and r["n"] == n]; s = [r for r in d if r["arm"] == "S" and r["n"] == n]
    if m and s:
        mc = sum(r["cost"] for r in m) / len(m); sc = sum(r["cost"] for r in s) / len(s)
        print(f"{n} combinations: multi-agent costs {mc/sc:.2f}x the single agent; supervisor share of M cost {sum(overhead_share(r['rc']) for r in m)/len(m):.3f}; workers per run {sum(r['workers'] for r in m)/len(m):.2f}")
# paired by (q, rep)
idx = {(r["q"], r["rep"], r["arm"]): r for r in d}; ratios = []
for (q, rep, arm), r in idx.items():
    if arm == "M" and (q, rep, "S") in idx: ratios.append(r["cost"] / idx[(q, rep, "S")]["cost"])
print(f"paired cost ratio M/S over {len(ratios)} pairs: median {quantile(ratios,.5):.2f} min {min(ratios):.2f} max {max(ratios):.2f}")
tot_m = sum(r["cost"] for r in d if r["arm"] == "M"); ok_m = sum(r["ok"] for r in d if r["arm"] == "M"); tot_s = sum(r["cost"] for r in d if r["arm"] == "S"); ok_s = sum(r["ok"] for r in d if r["arm"] == "S")
if ok_m and ok_s: print(f"cost per correct answer: single ${tot_s/ok_s:.5f}, multi ${tot_m/ok_m:.5f}")
