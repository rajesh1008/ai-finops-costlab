#!/usr/bin/env python3
"""Chapter 27: arithmetic over ladder-lab-2026-11-10.json (no API). Placeholder rates: haiku-4-5 $1/$5, haiku-5-5 $0.10/$0.50 per M tokens (costlab.prices).
Part 1: per-rung cost and accuracy by template. Part 2: replay a SYNTHETIC day (Zipf-repeating stream over the 120 measured questions, 5,000 requests, 8 percent of clauses revised so cached answers can be stale) under three policies and four budgets, 200 seeds each."""
import json, random, statistics as st
from pathlib import Path
from costlab.ladder import *
RUNS = Path(__file__).resolve().parents[1] / "runs"
d = json.load(open(RUNS / "ladder-lab-2026-11-10.json")); Q = d["questions"]; R = {"full": (1.0, 5.0), "reduced": (0.10, 0.50)}
by = {("full", r["q"]): r for r in d["results"] if r["rung"] == "full"}; by.update({("reduced", r["q"]): r for r in d["results"] if r["rung"] == "reduced"})
def cost(r, rung): return sum(usd(s["in"], s["out"], R[rung]) for s in r["steps"])
from costlab.retrieval import BM25
C = clauses(); bm = BM25([c["text"] for c in C])
det = {}
for qi, q in enumerate(Q):
    a = deterministic_answer(q["q"], bm, C); det[qi] = None if a is None else score(a, q["gold"])
print("Part 1: measured rungs (120 questions; templates A 40%, B 30%, C 30% by design)")
cm = {}
for rung in ("full", "reduced", "deterministic"):
    ok = {t: [0, 0] for t in "ABC"}; cs = []; ab = 0
    for qi, q in enumerate(Q):
        if rung == "deterministic":
            if det[qi] is None: ab += 1; ok[q["t"]][1] += 1; continue
            ok[q["t"]][0] += int(det[qi]); ok[q["t"]][1] += 1; cs.append(0.0)
        else:
            r = by[(rung, qi)]; ok[q["t"]][0] += int(r["ok"]); ok[q["t"]][1] += 1; cs.append(cost(r, rung))
    n = len(Q); tot = sum(v[0] for v in ok.values()); cm[rung] = (sum(cs) / len(cs)) if cs else 0.0
    lo, hi = wilson(tot, n)
    print(f"  {rung:13s} mean cost ${sum(cs)/max(len(cs),1) if rung!='deterministic' else 0:.6f}  correct {tot}/{n} = {tot/n:.3f} (95% Wilson {lo:.3f} to {hi:.3f})  abstained {ab}  by template " + " ".join(f"{t} {v[0]}/{v[1]}" for t, v in ok.items()))
f = [cost(by[("full", i)], "full") for i in range(len(Q))]; r_ = [cost(by[("reduced", i)], "reduced") for i in range(len(Q))]
print(f"  full steps mean {st.mean(len(by[('full', i)]['steps']) for i in range(len(Q))):.2f}; cost ratio full/reduced (means) {st.mean(f)/st.mean(r_):.1f}x")
cm["deterministic"] = 0.0
print("  reduced rung wrong answers (not abstentions):", sum(1 for i in range(len(Q)) if not by[("reduced", i)]["ok"] and "cannot" not in by[("reduced", i)]["answer"].lower()), "; abstained ('cannot answer'):", sum(1 for i in range(len(Q)) if "cannot" in by[("reduced", i)]["answer"].lower()))
print("  full rung wrong:", sum(1 for i in range(len(Q)) if not by[("full", i)]["ok"]))
# Part 2
rnd0 = random.Random(5); edited = set(rnd0.sample(range(1, 161), 13))
table = {}
for qi, q in enumerate(Q):
    stale = any(n in edited for n in q["needs"])
    table[qi] = {"key": q["q"], "stale": stale, "full": (cost(by[("full", qi)], "full"), by[("full", qi)]["ok"]), "reduced": (cost(by[("reduced", qi)], "reduced"), (None if "cannot" in by[("reduced", qi)]["answer"].lower() else by[("reduced", qi)]["ok"])),
                 "deterministic": (0.0, det[qi])}
print("\nPart 2: SYNTHETIC day, 5,000 requests, Zipf over a universe of distinct questions that reuse the 120 measured outcomes; 13 of 160 clauses revised, so", sum(t["stale"] for t in table.values()), "of the 120 measured questions have a stale cached answer")
N = 5000; U = 1500
def universe(U):
    """U distinct SYNTHETIC question keys; key u reuses the measured outcome of question u mod 120. Repeats (cache hits) come from the Zipf stream over the U keys."""
    return {u: dict(table[u % len(Q)], key=f"u{u}") for u in range(U)}
def one(policy, frac, seed, s=0.9, U=U):
    T = universe(U); stream = zipf_stream(N, U, s, seed); base = sum(T[q]["full"][0] for q in stream)
    return run_ladder(stream, T, frac * base, policy, dict(cm, _miss=0.21)), base
print(f" (universe of {U} distinct questions, Zipf s=0.9)")
for frac in (1.0, 0.5, 0.25, 0.10):
    print(f" budget = {int(frac*100)}% of the no-cache all-full cost")
    for pol in ("cliff", "cliff_cache", "ladder_naive", "ladder", "ladder_prior"):
        rs = [one(pol, frac, sd) for sd in range(100)]
        c = st.mean(r[0]["correct"] for r in rs) / N; w = st.mean(r[0]["wrong"] for r in rs) / N; o = st.mean(r[0]["off"] for r in rs) / N; sp = st.mean(r[0]["spend"] for r in rs); b = st.mean(r[1] for r in rs)
        br = {k: st.mean(r[0]["by_rung"][k] for r in rs) / N for k in RUNGS}
        print(f"   {pol:12s} correct {c:.3f} wrong {w:.3f} off {o:.3f}  spend ${sp:.2f} of budget ${frac*b:.2f}  rung shares " + " ".join(f"{k} {v:.2f}" for k, v in br.items()) + f"  off in last fifth of day {st.mean(r[0]['off_last_fifth'] for r in rs)/(N*0.2):.2f}")
print("\nCache share of requests by universe size (ladder, 100% budget) and Zipf skew:")
for UU in (500, 1500, 5000):
    for s_ in (0.6, 0.9, 1.2):
        rs = [one("ladder", 1.0, sd, s_, UU) for sd in range(40)]
        print(f"   U={UU:5d} s={s_}: cache share {st.mean(r[0]['by_rung']['cache'] for r in rs)/N:.3f}")
