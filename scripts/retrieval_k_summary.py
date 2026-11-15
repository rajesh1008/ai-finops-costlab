#!/usr/bin/env python3
"""Chapter 23: summary of the k sweep. Cost at the dated placeholder table for claude-haiku-4-5. No API."""
import json
from pathlib import Path
from costlab.estimate import estimate_usd
D = json.load(open(Path(__file__).resolve().parents[1] / "runs" / "retrieval-k-lab-2026-11-10.json")); M = "anthropic:claude-haiku-4-5-20251001"
print("k   recall@k  answered_exactly  mean_in_tokens  cost_per_1000_queries  cost_per_correct_answer  cut_off_at_max_tokens")
for k in (1, 2, 4, 8, 16, 0):
    rs = [r for r in D["results"] if r["k"] == k and r["ok"] is not None]; n = len(rs); ok = sum(r["ok"] for r in rs)
    cost = sum(estimate_usd(M, r["in"], r["out"]) for r in rs) / n
    rc = D["recall"].get(str(k)) if k else None
    print(f"{'all' if k == 0 else k:>3} {('%.3f' % rc) if rc is not None else '  -  ':>8}  {ok / n:16.3f}  {sum(r['in'] for r in rs) / n:14.0f}  ${cost * 1000:20.4f}  ${cost / max(ok / n, 1e-9):.6f}  {sum(r.get('cut', False) for r in rs)} of {n}")
