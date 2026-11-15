#!/usr/bin/env python3
"""Chapter 19: summarise the two real labs from their recorded logs (no API)."""
import json
from pathlib import Path
from collections import defaultdict
R = Path(__file__).resolve().parents[1] / "runs"
def load(name):
    return [json.loads(l) for l in (R / name).read_text().splitlines()]
print("== output constraint (Haiku 5.5, 30 problems)")
recs = load("output-constraint-2026-11-10.jsonl"); ans = json.loads((R / "output-constraint-answers-2026-11-10.json").read_text())
by = defaultdict(list)
for r in recs: by[r["feature"]].append(r)
ok = defaultdict(int)
for a in ans: ok[a["v"]] += a["ok"]
print("variant   n  correct  avg_out  avg_usd_call  total_usd")
for v in ("sentence", "steps", "number"):
    rs = by["oc-" + v]; n = len(rs)
    print(f"{v:9s} {n:2d}  {ok[v]:2d}/{n}   {sum(r['output_tokens'] for r in rs)/n:6.1f}  {sum(r['estimated_cost_usd'] for r in rs)/n:.6f}   {sum(r['estimated_cost_usd'] for r in rs):.5f}")
print("\n== prompt diet (Haiku 4.5, 60 tickets, no caching)")
recs = load("prompt-diet-2026-11-10.jsonl"); ans = json.loads((R / "prompt-diet-answers-2026-11-10.json").read_text())
by = defaultdict(list)
for r in recs: by[r["feature"]].append(r)
ok = defaultdict(int); hard_ok = defaultdict(int)
from costlab.triage import make_tickets
hard_ids = {t["id"] for t in make_tickets(60) if t["text"] not in sum(([x for x in v] for v in __import__("costlab.triage", fromlist=["CLEAR"]).CLEAR.values()), [])}
for a in ans:
    ok[a["v"]] += a["pred"] == a["label"]
    if a["id"] in hard_ids: hard_ok[a["v"]] += a["pred"] == a["label"]
print(f"hard tickets: {len(hard_ids)}")
print("variant    n  correct  hard_correct  avg_input  usd_per_call  usd_per_1000_calls")
for v in ("lean", "plus800", "plus3000"):
    rs = by["diet-" + v]; n = len(rs)
    print(f"{v:9s} {n:3d}  {ok[v]:2d}/{n}   {hard_ok[v]:2d}/{len(hard_ids)}      {sum(r['input_tokens'] for r in rs)/n:7.0f}   {sum(r['estimated_cost_usd'] for r in rs)/n:.6f}     {1000*sum(r['estimated_cost_usd'] for r in rs)/n:.3f}")
