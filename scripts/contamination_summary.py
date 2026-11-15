#!/usr/bin/env python3
"""Chapter 22: summary of the contamination lab plus CCRM arithmetic. No API."""
import json
from pathlib import Path
from costlab.retries import ccrm_success, clean_success, fit_p1, cost_per_success, simulate, expected_attempts
from costlab.estimate import estimate_usd
R = [r for r in json.load(open(Path(__file__).resolve().parents[1] / "runs" / "contamination-lab-2026-11-10.json")) if r["ok"] is not None]
M = "anthropic:claude-haiku-4-5-20251001"
st = {}
for cond in ("clean", "same", "same_log", "same_nofb", "clean_hint"):
    rs = [r for r in R if r["cond"] == cond]; n = len(rs); k = sum(r["ok"] for r in rs)
    cost = sum(estimate_usd(M, r["in"], r["out"]) for r in rs) / n
    rw = sum(r.get("repeat_wrong", False) for r in rs)
    st[cond] = (k / n, cost); print(f"{cond:10s} n={n:3d} correct={k/n:.3f} mean_in={sum(r['in'] for r in rs)/n:6.1f} mean_out={sum(r['out'] for r in rs)/n:5.1f} cost_per_call=${cost:.6f} repeated_the_wrong_number={rw}")
p0, p1, pc = st["clean"][0], st["same"][0], st["clean"][0]
print(f"\nMeasured p0 (clean) {p0:.3f}; p1 (same-context retry after a wrong attempt) {p1:.3f}; p1 with failed log {st['same_log'][0]:.3f}; no feedback {st['same_nofb'][0]:.3f}; clean with hint {st['clean_hint'][0]:.3f}")
print("pass@k   clean-restart   CCRM(same context)")
for k in (1, 2, 3, 5): print(f"  k={k}   {clean_success(p0, k):.3f}           {ccrm_success(p0, p1, k):.3f}")
print("\nPaper check (arXiv 2605.08563 inputs: p0=0.761, pass@3=0.812):  p1 = %.3f" % fit_p1(0.761, 0.812, 3),
      " IID pass@3 = %.3f  CCRM pass@3 = %.3f" % (clean_success(0.761, 3), ccrm_success(0.761, fit_p1(0.761, 0.812, 3), 3)))
print("Monte Carlo check of the formula (p0=0.7, p1=0.2, k=3): formula %.3f  simulation %.3f" % (ccrm_success(0.7, 0.2, 3), simulate(0.7, 0.2, 3)))
print("\nExpected spend per success at the measured per-call costs, k=3 (attempt 1 is the clean call; retries cost what that condition's calls cost, history not re-priced beyond that):")
for nm, cond in (("clean restart", "clean"), ("rejected, same context", "same"), ("double-check, same context", "same_nofb"), ("rejected, same context + failed log", "same_log"), ("clean restart with hint", "clean_hint")):
    pr, cr = st[cond]
    print(f"  {nm:36s} p_retry={pr:.3f}  attempts used {expected_attempts(p0, pr, 3):.2f}  success within 3 {ccrm_success(p0, pr, 3):.3f}  cost per success ${cost_per_success(p0, pr, 3, st['clean'][1], cr):.6f}")
