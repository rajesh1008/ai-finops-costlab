#!/usr/bin/env python3
"""Chapter 7 failure injection on REAL lab records: blank the session id on the three most expensive sessions."""
import json
from pathlib import Path
from collections import defaultdict
runs = Path(__file__).resolve().parent.parent / "runs"
recs = [json.loads(l) for l in (runs / "meter-2026-11-10.jsonl").read_text().splitlines()]
def by_session(blank=()):
    t = defaultdict(float); n = defaultdict(int)
    for d in recs:
        s = json.loads(d["notes"])["session_id"]
        s = None if s in blank else s
        t[s] += d["estimated_cost_usd"]; n[s] += 1
    return t, n
t, n = by_session()
top3 = [s for s, _ in sorted(t.items(), key=lambda kv: -kv[1])[:3]]
print("most expensive three:", ", ".join(f"{s} ${t[s]:.5f}" for s in top3))
t2, n2 = by_session(set(top3))
mx = max(t2.items(), key=lambda kv: kv[1])
print(f"after blanking: sessions in table {len(t2)} (was {len(t)}); largest group {mx[0]} ${mx[1]:.5f} from {n2[mx[0]]} calls")
print(f"share of calls with no session id: {n2[None]}/{len(recs)} = {n2[None]/len(recs):.1%}")
print(f"largest before ${max(t.values()):.5f}; after / before = {mx[1]/max(t.values()):.1f}x")
