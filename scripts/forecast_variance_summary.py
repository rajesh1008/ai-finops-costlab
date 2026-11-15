#!/usr/bin/env python3
"""Chapter 45 summary of runs/forecast-variance-lab-2026-11-11.json: per-call output variation, interval coverage from a short history, volume-rate decomposition."""
import json, statistics as st
from pathlib import Path
from collections import defaultdict
from costlab.forecastvar import cv, call_cost, bootstrap_total_interval, normal_total_interval, point_total, coverage
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
R = json.loads((Path(__file__).resolve().parents[1] / "runs" / "forecast-variance-lab-2026-11-11.json").read_text())["results"]
PK = {"h45": "anthropic:claude-haiku-4-5-20251001", "h55": "anthropic:claude-haiku-5-5"}
print("calls", len(R), "api_errors", sum(r["stop"] == "api_error" for r in R), "hit max_tokens", {m: sum(r["stop"] == "max_tokens" for r in R if r["m"] == m) for m in PK})
def pointnorm(h, n): p = point_total(h, n); return p, p
for m in PK:
    rr = [r for r in R if r["m"] == m and r["tout"] is not None]
    cost = [call_cost(r["tin"], r["tout"], P[PK[m]]["input"], P[PK[m]]["output"]) for r in rr]
    byp = defaultdict(list)
    for r, c in zip(rr, cost): byp[r["id"]].append((r["tout"], c))
    within = st.fmean(cv([x[0] for x in v]) for v in byp.values())
    pm = {i: st.fmean(x[0] for x in v) for i, v in byp.items()}
    allout = [r["tout"] for r in rr]
    print(f"\n{m}: mean out {st.fmean(allout):.0f} tokens, overall CV {cv(allout):.2f}, mean within-prompt CV {within:.2f}, mean cost/call ${st.fmean(cost):.6f}")
    bytype = defaultdict(list)
    for r in rr: bytype[r["type"]].append(r["tout"])
    print("  mean output by type:", {t: round(st.fmean(v)) for t, v in bytype.items()})
    print("  p50/p95 cost per call ratio:", round(sorted(cost)[len(cost) // 2] and sorted(cost)[int(.95 * len(cost))] / sorted(cost)[len(cost) // 2], 2))
    # forecast coverage: population = per-type call costs; history of 20 calls, future month 200 calls (sampling with replacement from a pool of 25 per type is limited, so future_n = 5 with pools of 25)
    types = sorted({r["type"] for r in rr}); groups = [[c for r, c in zip(rr, cost) if r["type"] == t] for t in types]
    for hist_n in (5, 10):
        for name, meth in (("point only", pointnorm), ("normal 90%", normal_total_interval), ("bootstrap 90%", bootstrap_total_interval)):
            cov, w = coverage(groups, hist_n, 25 - hist_n if hist_n == 5 else 15, meth, trials=2000)
            print(f"  history {hist_n:>2} calls, {name:14}: covered {cov:.3f}, width/actual {w:.3f}")
    # mix shift: a forecast made on equal type weights vs actual mix 50% 'explain'/'reply' heavy
    tm = {t: st.fmean(g) for t, g in zip(types, groups)}
    base = st.fmean(tm.values()); heavy = {t: (3 if t in ("explain", "plan", "compare") else 1) for t in types}
    mix = sum(tm[t] * heavy[t] for t in types) / sum(heavy.values())
    print(f"  mix shift: equal-weight mean ${base:.6f}/call vs mix weighted 3x toward explain/plan/compare ${mix:.6f}/call ({(mix / base - 1) * 100:+.1f}%)")
