#!/usr/bin/env python3
"""Chapter 7: tail summary of cost per session. Part 1 real lab data (10 sessions). Part 2 a SYNTHETIC day."""
import json
from pathlib import Path
from costlab.runs_graph import Call, rollup, session_costs, tail_summary, synthetic_day

runs = Path(__file__).resolve().parent.parent / "runs"
real = []
for l in (runs / "meter-2026-11-10.jsonl").read_text().splitlines():
    d = json.loads(l); n = json.loads(d["notes"])
    real.append(Call(d["record_id"], n["session_id"], n["session_id"], None, d["estimated_cost_usd"]))
sc = session_costs(real)
t = tail_summary(list(sc.values()))
print("REAL lab sessions (n=10, too few for any percentile claim):")
print(f"  mean ${t['mean']:.5f} median ${t['median']:.5f} max ${t['max']:.5f} max/median {t['max']/t['median']:.1f}x")

print("\nNested rollup example (SYNTHETIC trace: parent run, two subagent runs, one retry):")
trace = [Call("a", "s1", "root", None, 0.010), Call("b", "s1", "sub1", "root", 0.030),
         Call("c", "s1", "sub2", "root", 0.020), Call("d", "s1", "sub2", "root", 0.020, "retry"),
         Call("e", "s1", "sub1", "root", 0.010)]
r = rollup(trace)
for k in ("root", "sub1", "sub2"):
    print(f"  {k:5s} ${r[k]:.3f}")
print(f"  session total ${session_costs(trace)['s1']:.3f}; root rollup equals session total: {abs(r['root'] - session_costs(trace)['s1']) < 1e-12}")

print("\nSYNTHETIC day, 4,000 sessions, seed 7 (shape check only, not a Fieldstone measurement):")
for label, rate in (("no runaway sessions", 0.0), ("1 percent runaway at about 60x", 0.01)):
    s = tail_summary(synthetic_day(loop_rate=rate))
    print(f"  {label}: median ${s['median']:.3f} mean ${s['mean']:.3f} p95 ${s['p95']:.3f} p99 ${s['p99']:.3f} "
          f"max ${s['max']:.2f}; top 3 percent of sessions = {s['top3pct_share']:.1%} of spend; mean/median {s['mean']/s['median']:.2f}")
