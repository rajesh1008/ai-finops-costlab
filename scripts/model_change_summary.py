#!/usr/bin/env python3
"""Chapter 35 summary of runs/model-change-lab-2026-11-11.json: outcome classes per arm, cost per call and per good outcome, item-level flips, break-even failure cost, canary replay.
Failure cost, monthly volume and the canary alpha are ASSUMED. Prices are the dated placeholders in costlab/prices.py."""
import json, statistics, math
from pathlib import Path
from collections import Counter
from costlab.modelchange import *
from costlab.ladder import wilson
R = Path(__file__).resolve().parents[1] / "runs"
def main(shim=True):
    d = json.load(open(R / "model-change-lab-2026-11-11.json")); Q = d["questions"]; arms = list(d["arms"]); K = d["K"]
    print("calls", len(d["results"]), "errors", sum(r["error"] is not None for r in d["results"]), "answerable questions", sum(q["answerable"] for q in Q), "of", len(Q))
    st = {}
    for a in arms:
        rs = [r for r in d["results"] if r["arm"] == a and not r["error"]]; cl = []
        for r in rs: cl.append(classify(r["text"], Q[r["q"]]["gold"], Q[r["q"]]["answerable"], shim))
        cnt = Counter(cl); n = len(rs); cost = sum(call_cost(d["arms"][a][0], r["in"], r["out"]) for r in rs); good = sum(c in GOOD for c in cl)
        trunc = sum(1 for r, c in zip(rs, cl) if c == "unparsed" and r["stop"] == "max_tokens"); empty = sum(1 for r, c in zip(rs, cl) if c == "unparsed" and not r["text"].strip())
        fail = (cnt["unparsed"] + cnt["wrong"]) / n
        st[a] = {"n": n, "cost": cost, "good": good, "fail": fail, "cl": cl, "rs": rs}
        lo, hi = wilson(good, n)
        print(f"{a:<3} {d['arms'][a][0][:22]:<22} n={n} correct {cnt['correct']:3d} correct_decline {cnt['correct_decline']:3d} wrong_decline {cnt['wrong_decline']:3d} wrong {cnt['wrong']:3d} unparsed {cnt['unparsed']:3d} (max_tokens {trunc}, empty {empty}) good {good/n*100:5.1f}% [{lo*100:.1f}-{hi*100:.1f}]  mean out {statistics.mean(r['out'] for r in rs):6.1f}  $/1000 calls {cost/n*1000:.4f}  $/1000 good {cost/max(1,good)*1000:.4f}  p50 s {statistics.median(r['secs'] for r in rs):.2f}")
    a = st["A"]
    for b in arms[1:]:
        s = st[b]; print(f"{b}: price per call vs A {a['cost']/a['n'] / (s['cost']/s['n']):.2f}x cheaper; per good outcome {(a['cost']/a['good'])/(s['cost']/s['good']):.2f}x; failure rate A {a['fail']*100:.1f}% B {s['fail']*100:.1f}%; break-even failure cost per failure ${break_even_failure_cost(a['cost']/a['n'], a['fail'], s['cost']/s['n'], s['fail']) or 0:.6f}")
    b0 = st["B0"]
    for b in ("B1",):
        s = st[b]; saved = b0["cost"]/b0["n"] - s["cost"]/s["n"]; extra = (sum(c == "unparsed" for c in s["cl"]) - sum(c == "unparsed" for c in b0["cl"])) / s["n"]
        print(f"{b} against B0: saving per call ${saved:.7f} ({saved/(b0['cost']/b0['n'])*100:.1f}%); extra format failures {extra*100:.1f}% of calls; break-even cost per format failure ${saved/extra:.7f}")
    print("\nItem level (good outcomes out of 3 per question)")
    def gc(arm): 
        g = {}
        for r, c in zip(st[arm]["rs"], st[arm]["cl"]): g[r["q"]] = g.get(r["q"], 0) + (c in GOOD)
        return g
    ga = gc("A")
    for b in arms[1:]:
        gb = gc(b); reg = sum(1 for q in range(len(Q)) if ga.get(q, 0) >= 2 and gb.get(q, 0) <= 1); imp = sum(1 for q in range(len(Q)) if gb.get(q, 0) >= 2 and ga.get(q, 0) <= 1)
        print(f"  A to {b}: questions where A good in >=2 of 3 and {b} in <=1: {reg}; the reverse: {imp}")
    print("\nWhere the B0 failures sit by template and answerability")
    for t in "ABC":
        idx = [i for i, q in enumerate(Q) if q["t"] == t]; rs = [(r, c) for r, c in zip(st["B0"]["rs"], st["B0"]["cl"]) if r["q"] in idx]
        print(f"  template {t}: calls {len(rs)} unparsed {sum(c=='unparsed' for _, c in rs)} ({sum(c=='unparsed' for _, c in rs)/len(rs)*100:.0f}%)")
    if not shim: return
    print("\nCanary replay, one gate per failure class (ASSUMED: alpha 0.01, baseline p0 = max(A rate for the class, 1%), 1,200,000 requests a month, 5% canary = 60,000 a month)")
    for cls, label in (("unparsed", "format failures (unparsed)"), ("wrong", "confident wrong (wrong + wrong_decline)")):
        def isbad(c): return c == "unparsed" if cls == "unparsed" else c in ("wrong", "wrong_decline")
        p0 = max(sum(isbad(c) for c in st["A"]["cl"]) / st["A"]["n"], 0.01); print(f"  gate on {label}: baseline from A = {sum(isbad(c) for c in st['A']['cl'])/st['A']['n']*100:.1f}%, p0 used {p0*100:.1f}%")
        for b in arms[1:]:
            bad = [1 if isbad(c) else 0 for c in st[b]["cl"]]; rate = sum(bad) / len(bad)
            if sum(bad) == 0: print(f"    {b}: rate 0.0%, gate does not fire"); continue
            dt = canary_detect(bad, p0, max_n=600, trials=1500, seed=5); med = dt[len(dt)//2]; p90 = dt[int(len(dt)*0.9)]; miss = sum(1 for x in dt if x > 600)
            print(f"    {b}: rate {rate*100:.1f}%; requests to detect median {med}, p90 {p90}, not detected within 600: {miss} of {len(dt)}")
    print("\nRisk-adjusted cost per 1000 calls: cost + unparsed x F_loud + (wrong + wrong_decline) x F_silent (ASSUMED values)")
    def rate(x, f): return sum(1 for c in st[x]["cl"] if f(c)) / st[x]["n"]
    for FL, FS in ((0.0, 0.0), (0.002, 0.05), (0.01, 0.25), (0.05, 1.00)):
        print(f"  F_loud ${FL:.3f}, F_silent ${FS:.2f}: " + "  ".join(f"{x} {(st[x]['cost']/st[x]['n'] + rate(x, lambda c: c=='unparsed')*FL + rate(x, lambda c: c in ('wrong','wrong_decline'))*FS)*1000:8.3f}" for x in arms))
if __name__ == "__main__":
    import sys
    print("=== reading 1: strict json.loads on the raw reply (no shim) ==="); main(False)
    print("\n=== reading 2: the incumbent's fence-stripping shim applied to every arm ==="); main(True)
