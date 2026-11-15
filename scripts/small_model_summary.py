#!/usr/bin/env python3
"""Chapter 21: summary over the recorded lab. Student is naive Bayes trained on teacher labels vs gold labels at several sizes. Arithmetic only, no API."""
import json, os, sys
from pathlib import Path
from costlab.smallmodels import NB, accuracy, breakeven_requests, breakeven_months, utilisation_cost_per_1k
from costlab.estimate import estimate_usd
D = json.load(open(Path(__file__).resolve().parents[1] / "runs" / ("small-model-lab-hard-2026-11-10.json" if os.environ.get("HARD") == "1" else "small-model-lab-2026-11-10.json")))
T = {t["id"]: t for t in D["tickets"]}; R = D["results"]
arm = lambda a: {r["id"]: r for r in R if r["arm"] == a}
teach, small, again = arm("teacher"), arm("small"), arm("teacher_again")
train = [t for t in D["tickets"][:400]]; test = D["tickets"][400:]
gold_test = [t["label"] for t in test]
def acc_of(a): 
    ids = [t["id"] for t in test if a.get(t["id"], {}).get("pred")]
    return accuracy([a[i]["pred"] for i in ids], [T[i]["label"] for i in ids]), len(ids)
print("teacher noise on train labels vs gold: %.3f" % accuracy([teach[t["id"]]["pred"] for t in train], [t["label"] for t in train]))
for name, a in (("teacher claude-haiku-4-5", teach), ("small claude-haiku-5-5", small)):
    ac, n = acc_of(a); print(f"{name}: accuracy {ac:.3f} on {n} test tickets")
ids = [t["id"] for t in test[:100] if teach[t["id"]]["pred"] and again[t["id"]]["pred"]]
print("teacher self-agreement (same prompt, default temperature, 100 tickets): %.3f" % (sum(teach[i]["pred"] == again[i]["pred"] for i in ids) / len(ids)))
print("\nstudent (naive Bayes, no API) accuracy on the 200 test tickets by training size and label source")
print("n_train  teacher_labels  gold_labels  agreement_with_teacher_on_test")
for n in (25, 50, 100, 200, 400):
    sub = train[:n]
    s_t = NB().fit([t["text"] for t in sub], [teach[t["id"]]["pred"] or t["label"] for t in sub])
    s_g = NB().fit([t["text"] for t in sub], [t["label"] for t in sub])
    pt = [s_t.predict(t["text"]) for t in test]; pg = [s_g.predict(t["text"]) for t in test]
    ag = accuracy(pt, [teach[t["id"]]["pred"] for t in test])
    print(f"{n:7d}  {accuracy(pt, gold_test):14.3f}  {accuracy(pg, gold_test):11.3f}  {ag:10.3f}")
def cost(a, model):
    rs = [r for r in a.values() if r.get("pred")]; ti = sum(r["in"] for r in rs); to = sum(r["out"] for r in rs)
    return estimate_usd("anthropic:" + model, ti, to) / len(rs) * 1000, ti / len(rs), to / len(rs)
for nm, a, m in (("teacher", teach, "claude-haiku-4-5-20251001"), ("small", small, "claude-haiku-5-5")):
    c1k, i, o = cost(a, m); print(f"\n{nm}: measured {i:.0f} in / {o:.1f} out tokens per call, cost per 1,000 calls ${c1k:.4f} at the dated placeholder table")
tc = cost(teach, "claude-haiku-4-5-20251001")[0]
print("\nBreak-even arithmetic (ASSUMED build cost $6,000, ASSUMED student serving $0.02 per 1,000 calls, teacher price above):")
cn, cw = tc / 1000, 0.02 / 1000
print("break-even requests:", f"{breakeven_requests(6000, cn, cw):,.0f}")
for vol in (20_000, 200_000, 2_000_000):
    sav = vol * (cn - cw); print(f"  {vol:>9,} requests a month: saving ${sav:,.0f}; AWS-form months (training $6,000, refresh $1,000 a quarter, 4 quarters): {breakeven_months(6000, 1000, 4, sav):.1f}")
print("\nDedicated GPU, ASSUMED $2.50 an hour and 50 requests a second at full load: cost per 1,000 requests by utilisation")
for u in (1.0, 0.5, 0.3, 0.1, 0.02): print(f"  U={u:4.2f}  ${utilisation_cost_per_1k(2.5, 50, u):.4f}")
