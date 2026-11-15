#!/usr/bin/env python3
"""Chapter 24: arithmetic over the recorded agent-run-lab JSON. No API. Rates are the haiku-4-5 placeholders in costlab.prices."""
import json
from collections import defaultdict
from pathlib import Path
from costlab.agentrun import run_cost, quantile, spread, repeat_spread, input_share_of_steps, cost_if_capped
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
import sys
NAME = sys.argv[1] if len(sys.argv) > 1 else "agent-run-lab-2026-11-10.json"
R = Path(__file__).resolve().parents[1] / "runs"; d = json.load(open(R / NAME)); res = [r for r in d["results"] if r["status"] != "api_error"]
p = P["anthropic:claude-haiku-4-5-20251001"]; ui, uo = p["input"], p["output"]
for r in res: r["cost"] = run_cost(r["steps"], ui, uo); r["n"] = len(r["steps"]); r["in"] = sum(s["in"] for s in r["steps"]); r["out"] = sum(s["out"] for s in r["steps"])
costs = [r["cost"] for r in res]
print(f"runs {len(res)} (api errors excluded: {len(d['results']) - len(res)}); status counts: " + ", ".join(f"{k}={sum(1 for r in res if r['status'] == k)}" for k in sorted({r['status'] for r in res})))
print(f"correct {sum(r['ok'] for r in res)}/{len(res)} = {sum(r['ok'] for r in res)/len(res):.3f}")
print(f"cost per run: mean ${sum(costs)/len(costs):.5f} p50 ${quantile(costs,.5):.5f} p90 ${quantile(costs,.9):.5f} max ${max(costs):.5f} min ${min(costs):.5f}")
s = spread(costs); print(f"spread across all runs: max/min {s['max_over_min']:.1f}x, p90/p50 {s['p90_over_p50']:.2f}x, mean/median {s['mean_over_median']:.2f}x")
print("steps per run: " + ", ".join(f"{k}:{sum(1 for r in res if r['n']==k)}" for k in sorted({r['n'] for r in res})))
print(f"input tokens share of total tokens {sum(r['in'] for r in res)/(sum(r['in'] for r in res)+sum(r['out'] for r in res)):.3f}; input share of dollars {sum(r['in'] for r in res)*ui/(sum(r['in'] for r in res)*ui+sum(r['out'] for r in res)*uo):.3f}")
print(f"mean share of billed input that re-reads the previous step: {sum(input_share_of_steps(r['steps']) for r in res)/len(res):.3f}")
for ok in (True, False):
    c = [r["cost"] for r in res if r["ok"] == ok]
    if c: print(f"{'correct' if ok else 'wrong  '} runs n={len(c)}: mean ${sum(c)/len(c):.5f} mean steps {sum(r['n'] for r in res if r['ok']==ok)/len(c):.2f}")
by = defaultdict(list)
for r in res: by[r["q"]].append(r["cost"])
rs = repeat_spread(by); print(f"repeat spread (same question, 3 runs): median max/min {quantile(rs,.5):.2f}x, p90 {quantile(rs,.9):.2f}x, worst {max(rs):.2f}x")
tmean = {q: sum(v)/len(v) for q, v in by.items()}; tm = sorted(tmean.values()); print(f"question-mean cost: cheapest ${tm[0]:.5f} dearest ${tm[-1]:.5f} ratio {tm[-1]/tm[0]:.1f}x")
base = 0.00032; print(f"single-call RAG at k=4 (Chapter 23, one combination): ${base:.5f}; agent mean is {sum(costs)/len(costs)/base:.1f}x, agent p90 is {quantile(costs,.9)/base:.1f}x")
print("per-step input tokens (mean over runs that reached the step): " + ", ".join(f"s{i+1}={sum(r['steps'][i]['in'] for r in res if len(r['steps'])>i)/sum(1 for r in res if len(r['steps'])>i):.0f}" for i in range(max(r["n"] for r in res)) if any(len(r["steps"]) > i for r in res)))
tot = sum(costs)
for cap in (quantile(costs,.5), quantile(costs,.8), quantile(costs,.95)):
    spent, cut = cost_if_capped(costs, cap); wrong_cut = sum(1 for r in res if r["cost"] > cap and r["ok"])
    print(f"cap ${cap:.5f}: runs cut {cut}, of which would have been correct {wrong_cut}; spend ${spent:.4f} vs ${tot:.4f} ({1-spent/tot:.1%} saved)")
if "n_pairs" in res[0]:
    for n in sorted({r["n_pairs"] for r in res}):
        g = [r for r in res if r["n_pairs"] == n]; c = [r["cost"] for r in g]
        print(f"{n} {'hops' if 'chain' in NAME else 'combinations'}: runs {len(g)} correct {sum(r['ok'] for r in g)/len(g):.3f} mean steps {sum(r['n'] for r in g)/len(g):.2f} mean cost ${sum(c)/len(c):.5f} p90 ${quantile(c,.9):.5f} max ${max(c):.5f}")
print(f"cost per correct answer: ${tot/max(1,sum(r['ok'] for r in res)):.5f}")
print("by step count: " + "; ".join(f"{k} steps n={sum(1 for r in res if r['n']==k)} mean ${sum(r['cost'] for r in res if r['n']==k)/sum(1 for r in res if r['n']==k):.5f}" for k in sorted({r['n'] for r in res})))
print("status: " + ", ".join(f"{k}={sum(1 for r in res if r['status']==k)}" for k in sorted({r['status'] for r in res})))
