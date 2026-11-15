#!/usr/bin/env python3
"""Ch44 follow-up summary of runs/loop-growth-lab-2026-11-11.json (offline): per-step input growth, the segment identity check, repeated-input share, cost at placeholder rates, and cost of step k versus steps 1 to k."""
import json, statistics as st
from pathlib import Path
from costlab.segments import trace_triple, total_from_triple, total, repeated_input_share, quadratic_fit
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
R = Path(__file__).resolve().parents[1] / "runs"; d = json.loads((R / "loop-growth-lab-2026-11-11.json").read_text())["results"]
PM = {"h45": "anthropic:claude-haiku-4-5-20251001", "h55": "anthropic:claude-haiku-5-5"}; lines = []
for m in ("h45", "h55"):
    rs = [r for r in d if r["m"] == m and not r["error"]]; p = P[PM[m]]
    steps = [len(r["calls"]) for r in rs]; ident = all(total_from_triple(trace_triple(r["calls"]), r["calls"][0][0]) == total(r["calls"]) for r in rs)
    ended = sum(1 for r in rs if r.get("ended_with_text"))
    first = st.mean(r["calls"][0][0] for r in rs); last = st.mean(r["calls"][-1][0] for r in rs)
    shares = [repeated_input_share(r["calls"]) for r in rs]
    cost = [sum(i * p["input"] + o * p["output"] for i, o in r["calls"]) / 1e6 for r in rs]
    g = [quadratic_fit(r["calls"])[0] for r in rs]
    inp = [sum(i for i, _ in r["calls"]) for r in rs]; outp = [sum(o for _, o in r["calls"]) for r in rs]
    lines.append(f"{m}: runs {len(rs)}, steps median {st.median(steps)} (min {min(steps)}, max {max(steps)}), ended with a text answer {ended}, segment identity holds on all runs: {ident}")
    lines.append(f"   input tokens call 1 mean {first:.0f}, last call mean {last:.0f}, mean growth per call {st.mean(g):.0f} tokens; input share of all tokens {sum(inp)/(sum(inp)+sum(outp)):.3f}; share of tokens that is input after call 1 {st.mean(shares):.3f}")
    lines.append(f"   cost per run at placeholder rates: mean ${st.mean(cost):.5f}, max ${max(cost):.5f}")
    full = [r for r in rs if len(r["calls"]) == 20]
    if full:
        c = full[0]["calls"]; cum = []; t = 0
        for i, o in c: t += i + o; cum.append(t)
        lines.append(f"   one 20-step run: tokens at step 5 {cum[4]}, step 10 {cum[9]}, step 20 {cum[19]}; step-20 call alone {sum(c[19])}; ratio of last-10 steps to first-10 steps {(cum[19]-cum[9])/cum[9]:.2f}")
(R / "loop-growth-summary-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
