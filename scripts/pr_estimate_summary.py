#!/usr/bin/env python3
"""Chapter 39 summary. Actual billed cost per call (placeholder rates) against three estimators, then the PR flags each would raise. Contract discount of 15 percent is ASSUMED."""
import json, statistics
from pathlib import Path
from collections import defaultdict
from costlab.showback import call_usd
from costlab.prestimate import *
R = Path(__file__).resolve().parents[1] / "runs"
d = json.load(open(R / "pr-estimate-lab-2026-11-11.json"))["results"]
by = defaultdict(list)
for r in d: by[r["conf"]].append(r)
DISC = 0.15; ASSUMED_OUT = 100  # a PR bot's flat guess for output tokens
rows = {}
print(f"calls {len(d)}, errors {sum(1 for r in d if r['error'])}")
print(f"{'config':<10} {'in tok':>7} {'out med':>8} {'writes':>6} {'reads':>6} {'actual $/call (contract)':>25} {'E1 list':>9} {'E2 contract':>11} {'E3 cache-aware':>14} {'E4 +meter out':>13} {'E5 +min length':>14}")
base_out = {}
for name, rs in by.items():
    rs = [r for r in rs if not r["error"]]
    model = rs[0]["model"]
    cost = lambda r: call_usd(model, r["in"], r["out"], r["cr"], r["cw"]) * (1 - DISC)
    act = statistics.mean(cost(r) for r in rs)
    tin = statistics.mean(r["count"] for r in rs); outm = statistics.median(r["out"] for r in rs)
    writes = sum(1 for r in rs if r["cw"] > 0); reads = sum(1 for r in rs if r["cr"] > 0)
    SUF = 15  # tokens of question in the suffix, as a PR bot would measure
    MINC = {"claude-haiku-4-5-20251001": 4096, "claude-haiku-5-5": 512}  # documented minimum cacheable lengths (Chapter 18, page opened 10 November)
    cache_on = rs[0]["cache"]
    pre_est = tin - SUF
    e1 = est_list(tin, ASSUMED_OUT, model)                      # list price, no contract, no cache
    e2 = est_list(tin, ASSUMED_OUT, model, DISC)                # contracted price, no cache
    e3 = est_cache_aware(pre_est, SUF, ASSUMED_OUT, model, 15, DISC, cache=cache_on)   # assumes the cache engages whenever requested
    OUT_METER = 8  # median output tokens on the production meter (baseline config)
    e4 = est_cache_aware(pre_est, SUF, OUT_METER, model, 15, DISC, cache=cache_on)
    engages = cache_on and pre_est >= MINC[model]
    e5 = est_cache_aware(pre_est, SUF, OUT_METER, model, 15, DISC, cache=engages)
    outm = statistics.median(r["out"] for r in rs); writes = sum(1 for r in rs if r["cw"] > 0); reads = sum(1 for r in rs if r["cr"] > 0)
    rows[name] = (act, e1, e2, e3, e4, e5)
    print(f"{name:<10} {tin:7.0f} {outm:8.0f} {writes:6d} {reads:6d} {act*1000:>24.4f}k {e1*1000:9.4f} {e2*1000:11.4f} {e3*1000:14.4f} {e4*1000:13.4f} {e5*1000:14.4f}")
print("\nEstimator error against actual, percent (E1 list price, no cache, 100 output tokens; E2 contract price; E3 contract and cache-aware; E4 as E3 with the output length from the meter; E5 as E4 plus the minimum-cacheable-length check)")
for name, (a, e1, e2, e3, e4, e5) in rows.items():
    print(f"  {name:<10} E1 {error_pct(e1, a):+7.1f}  E2 {error_pct(e2, a):+7.1f}  E3 {error_pct(e3, a):+7.1f}  E4 {error_pct(e4, a):+7.1f}  E5 {error_pct(e5, a):+7.1f}")
print("\nPR flags (rise of more than 20 percent in cost per call against baseline M1-160-on, the production config)")
b = rows["M1-160-on"]
tp = fp = fn = tn = {1: 0}
res = {k: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for k in ("E1", "E2", "E3", "E4", "E5")}
for name, v in rows.items():
    if name == "M1-160-on": continue
    truth = flag(v[0], b[0])
    for k, i in (("E1", 1), ("E2", 2), ("E3", 3), ("E4", 4), ("E5", 5)):
        f = flag(v[i], b[i]); key = ("tp" if truth else "fp") if f else ("fn" if truth else "tn"); res[k][key] += 1
print("  truth: " + ", ".join(f"{n} {'FLAG' if flag(v[0], b[0]) else 'ok'} ({(v[0]/b[0]-1)*100:+.0f}%)" for n, v in rows.items() if n != 'M1-160-on'))
for k, c in res.items(): print(f"  {k}: caught {c['tp']}, missed {c['fn']}, false alarms {c['fp']}, correctly passed {c['tn']}")
