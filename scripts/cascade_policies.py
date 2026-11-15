#!/usr/bin/env python3
"""Chapter 17: evaluate routing/cascade policies over the answers recorded by cascade_lab.py. No API calls. Rates from costlab.prices
(vendor page, 10 Nov 2026). Cost of each answer = its own measured tokens at its model's rate."""
import json
from pathlib import Path
from costlab.cascade import make_problems, correct, agree
from costlab.estimate import estimate_usd

RUNS = Path(__file__).resolve().parents[1] / "runs"
rows = json.loads((RUNS / "cascade-answers-2026-11-10.json").read_text())
MODEL = {"H45": "anthropic:claude-haiku-4-5-20251001", "H55": "anthropic:claude-haiku-5-5", "S46": "anthropic:claude-sonnet-4-6"}
probs = make_problems()
by = {}
for r in rows:
    r["cost"] = estimate_usd(MODEL[r["m"]], r["in"], r["out"], 0, 0)
    r["ok"] = correct(r["text"], probs[r["id"]]["answer"])
    by.setdefault((r["id"], r["m"]), []).append(r)
N = len(probs)

print("SINGLE-MODEL RESULTS (30 problems, one sample counted per sample; avg tokens are measured)")
print(f"{'model':>5} {'samples':>8} {'correct':>8} {'rate':>7} {'avg in':>7} {'avg out':>8} {'$/call':>10}")
for m in ("H45", "H55", "S46"):
    rs = [r for r in rows if r["m"] == m]
    ok = sum(r["ok"] for r in rs)
    print(f"{m:>5} {len(rs):>8} {ok:>8} {ok/len(rs):>7.1%} {sum(r['in'] for r in rs)/len(rs):>7.1f} {sum(r['out'] for r in rs)/len(rs):>8.1f} {sum(r['cost'] for r in rs)/len(rs):>10.6f}")

def policy(first):
    """Two samples from `first`; if they agree, accept the first; else escalate to S46 (one sample). Cost includes both samples."""
    ok = cost = esc = 0
    for p in probs:
        a, b = by[(p["id"], first)][:2]
        cost += a["cost"] + b["cost"]
        if agree(a["text"], b["text"]):
            ok += a["ok"]
        else:
            s = by[(p["id"], "S46")][0]; cost += s["cost"]; ok += s["ok"]; esc += 1
    return ok / N, cost / N, esc / N

def single(m, k=0):
    ok = sum(by[(p["id"], m)][k]["ok"] for p in probs); cost = sum(by[(p["id"], m)][k]["cost"] for p in probs)
    return ok / N, cost / N

print("\nPOLICIES (per problem)")
print(f"{'policy':<34} {'accuracy':>9} {'$/problem':>11} {'escalated':>10}")
for name, m in (("always H45", "H45"), ("always H55", "H55"), ("always S46", "S46")):
    a, c = single(m); print(f"{name:<34} {a:>9.1%} {c:>11.6f} {'-':>10}")
for first in ("H45", "H55"):
    a, c, e = policy(first); print(f"{'2x '+first+' agree else S46':<34} {a:>9.1%} {c:>11.6f} {e:>10.1%}")
# an oracle that knows which problems the cheap model gets right (upper bound, not a real policy)
for first in ("H45", "H55"):
    ok = cost = 0
    for p in probs:
        a = by[(p["id"], first)][0]; cost += a["cost"]
        if a["ok"]: ok += 1
        else: s = by[(p["id"], "S46")][0]; cost += s["cost"]; ok += s["ok"]
    print(f"{'oracle '+first+' then S46 if wrong':<34} {ok/N:>9.1%} {cost/N:>11.6f} {'(bound)':>10}")

print("\nWhen the two cheap samples agree, how often are they right?")
for first in ("H45", "H55"):
    ag = [(by[(p['id'], first)][0], by[(p['id'], first)][1]) for p in probs if agree(*[x['text'] for x in by[(p['id'], first)][:2]])]
    right = sum(a['ok'] and b['ok'] for a, b in ag)
    print(f"  {first}: agreed on {len(ag)}/{N}; both correct on {right}/{len(ag)}")
