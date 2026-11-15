#!/usr/bin/env python3
"""Chapter 25 cheap-worker run: arithmetic over cheap-worker-lab and multi-agent-lab JSON. No API. Placeholder rates: haiku-4-5 for supervisor, haiku-5-5 for workers. Arm W = supervisor haiku-4-5 + haiku-5-5 workers; arms S and M from the original lab (all haiku-4-5)."""
import json
from pathlib import Path
from costlab.agentrun import run_cost, quantile
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
R = Path(__file__).resolve().parents[1] / "runs"
h4, h5 = P["anthropic:claude-haiku-4-5-20251001"], P["anthropic:claude-haiku-5-5"]
def cost(r, wp):
    t = 0.0
    for role, steps in r["roles"].items():
        pr = wp if role.startswith("worker") else h4
        t += run_cost(steps, pr["input"], pr["output"])
    return t
a = [r for r in json.load(open(R / "multi-agent-lab-2026-11-10.json"))["results"] if r["status"] != "api_error"]
w = json.load(open(R / "cheap-worker-lab-2026-11-10.json"))["results"]
print("W api_error", sum(r["status"] == "api_error" for r in w)); w = [r for r in w if r["status"] != "api_error"]
for r in a: r["cost"] = cost(r, h4)
for r in w: r["cost"] = cost(r, h5); r["wcost"] = sum(run_cost(s, h5["input"], h5["output"]) for k, s in r["roles"].items() if k.startswith("worker")); r["calls"] = sum(len(v) for v in r["roles"].values())
for r in a: r["calls"] = sum(len(v) for v in r["roles"].values())
def line(label, g):
    c = [r["cost"] for r in g]; print(f"{label}: runs {len(g)} correct {sum(r['ok'] for r in g)} mean cost ${sum(c)/len(c):.5f} max ${max(c):.5f} mean calls {sum(r['calls'] for r in g)/len(g):.2f}")
for arm, g in (("S single (haiku-4-5)", [r for r in a if r["arm"] == "S"]), ("M all haiku-4-5", [r for r in a if r["arm"] == "M"]), ("W cheap workers", w)):
    line(arm, g)
    for n in (2, 6): line(f"   {n} combinations", [r for r in g if r["n"] == n])
mm = sum(r["cost"] for r in a if r["arm"] == "M") / 60; ww = sum(r["cost"] for r in w) / len(w); ss = sum(r["cost"] for r in a if r["arm"] == "S") / 60
print(f"W/M cost ratio {ww/mm:.3f}; W/S cost ratio {ww/ss:.3f}; worker share of W cost {sum(r['wcost'] for r in w)/sum(r['cost'] for r in w):.3f}")
print("status W:", {k: sum(1 for r in w if r["status"] == k) for k in {r["status"] for r in w}})
wrong = [r for r in w if not r["ok"]]
print("wrong runs:", len(wrong), [(r["q"], r["n"], len(r.get("answer") or []), len(r["gold"])) for r in wrong][:12])
cs = [r for r in json.load(open(R / "cheap-single-lab-2026-11-10.json"))["results"] if r["status"] != "api_error"]
for r in cs: r["cost"] = run_cost(r["roles"]["single"], h5["input"], h5["output"]); r["calls"] = len(r["roles"]["single"])
line("S single (haiku-5-5, thinking off)", cs)
for n in (2, 6): line(f"   {n} combinations", [r for r in cs if r["n"] == n])
cc = sum(r["cost"] for r in cs) / len(cs); print(f"S5/S4 {cc/ss:.3f}; W / S5 {ww/cc:.2f}; M / S5 {mm/cc:.1f}; status S5:", {k: sum(1 for r in cs if r["status"] == k) for k in {r["status"] for r in cs}})
print("S5 wrong:", [(r["q"], r["n"], r["status"]) for r in cs if not r["ok"]])
