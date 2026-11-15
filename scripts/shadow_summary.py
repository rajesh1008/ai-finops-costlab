#!/usr/bin/env python3
"""Chapter 28: arithmetic over shadow-lab-2026-11-10.json (no API). Placeholder rates haiku-4-5 $1/$5, haiku-5-5 $0.10/$0.50 per M.
Part 1 paired comparison of incumbent and candidate on 300 measured questions. Part 2 SYNTHETIC shadow programs on a 3,000-requests-a-day assistant: sample fraction, decision rule, days to decide, spend, break-even; with and without an injected candidate regression."""
import json, random, statistics as st, math
from pathlib import Path
from costlab.ladder import usd, paired_diff, wilson
RUNS = Path(__file__).resolve().parents[1] / "runs"
d = json.load(open(RUNS / "shadow-lab-2026-11-10.json")); Q = d["questions"]; A, B = d["models"]["incumbent"], d["models"]["candidate"]; RATE = {A: (1.0, 5.0), B: (0.10, 0.50)}
by = {(r["model"], r["q"]): r for r in d["results"]}
a = [int(by[(A, i)]["ok"]) for i in range(len(Q))]; b = [int(by[(B, i)]["ok"]) for i in range(len(Q))]
ca = [usd(by[(A, i)]["in"], by[(A, i)]["out"], RATE[A]) for i in range(len(Q))]; cb = [usd(by[(B, i)]["in"], by[(B, i)]["out"], RATE[B]) for i in range(len(Q))]
print("Part 1: paired comparison, 300 SYNTHETIC questions (A 40%, B 30%, C 30% by design), one call each")
for name, x, c, m in (("incumbent haiku-4-5", a, ca, A), ("candidate haiku-5-5", b, cb, B)):
    lo, hi = wilson(sum(x), len(x)); print(f"  {name}: correct {sum(x)}/300 = {sum(x)/300:.3f} (Wilson {lo:.3f} to {hi:.3f}); mean cost ${st.mean(c):.6f}; mean in {st.mean(by[(m,i)]['in'] for i in range(300)):.0f} out {st.mean(by[(m,i)]['out'] for i in range(300)):.1f} tokens")
m, se, bw, aw = paired_diff(a, b)
print(f"  paired diff (candidate minus incumbent) {m:+.4f} (SE {se:.4f}); candidate-only right {bw}, incumbent-only right {aw}; 95% CI {m-1.96*se:+.4f} to {m+1.96*se:+.4f}; cost ratio incumbent/candidate {st.mean(ca)/st.mean(cb):.1f}x")
for t in "ABC":
    idx = [i for i, q in enumerate(Q) if q["t"] == t]; mm, ss, bw2, aw2 = paired_diff([a[i] for i in idx], [b[i] for i in idx])
    print(f"   template {t} (n={len(idx)}): incumbent {sum(a[i] for i in idx)}, candidate {sum(b[i] for i in idx)}, diff {mm:+.3f} (SE {ss:.3f}), candidate-only {bw2}, incumbent-only {aw2}")
print("  disagreement between the two answers' correctness:", sum(1 for x, y in zip(a, b) if x != y), "of 300")
N = 3000; DELTA = 0.03; HORIZON = 30; JUDGE = None
try:
    j = json.load(open(RUNS / "judge-lab-2026-11-10.json")); r = [x for x in j["results"] if x["judge"] == "ctx_h5" and x["error"] is None]
    JUDGE = st.mean(usd(x["in"], x["out"], (0.10, 0.50)) for x in r)
except Exception: pass
print(f"\nPart 2: SYNTHETIC programs. Assistant volume {N}/day (ILLUSTRATIVE). Non-inferiority margin {DELTA}. Decision each day on the cumulative sample: promote if the lower 95% bound of (candidate - incumbent) exceeds -{DELTA}; reject if the upper bound is below -{DELTA}; undecided at {HORIZON} days.")
print(f"  label cost per shadowed request: exact scorer $0 (golden-set style) or LLM judge ${JUDGE:.6f} (measured ctx_h5 mean at haiku-5-5 rates)" if JUDGE else "  judge cost unavailable")
MIN_DAY, MIN_N = 7, 200
def program(f, seed, regress=0.0, seg_gate=False):
    """Pre-registered rule: no decision before MIN_DAY days and MIN_N samples (a week covers the weekly cycle). With seg_gate, also reject when any template with at least 30 samples has its upper bound below -0.10."""
    rnd = random.Random(seed); n_day = int(N * f); xs = []; byt = {"A": [], "B": [], "C": []}
    for day in range(1, HORIZON + 1):
        for _ in range(n_day):
            i = rnd.randrange(len(Q)); y = b[i]
            if regress and Q[i]["t"] == "A" and y and rnd.random() < regress: y = 0
            xs.append(y - a[i]); byt[Q[i]["t"]].append(y - a[i])
        n = len(xs)
        if day < MIN_DAY or n < MIN_N: continue
        mu = sum(xs) / n; sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / (n - 1)); se = sd / math.sqrt(n)
        if seg_gate:
            for t, v in byt.items():
                if len(v) >= 30:
                    mt = sum(v) / len(v); st_ = math.sqrt(sum((x - mt) ** 2 for x in v) / (len(v) - 1) / len(v))
                    if mt + 1.96 * st_ < -0.10: return day, "reject", n
        if mu - 1.96 * se > -DELTA: return day, "promote", n
        if mu + 1.96 * se < -DELTA: return day, "reject", n
    return HORIZON, "undecided", len(xs)
saving_day = N * (st.mean(ca) - st.mean(cb))
print(f"  switching saves ${saving_day:.2f} a day at {N}/day (inference only, placeholder rates); incumbent inference ${N*st.mean(ca):.2f}/day, candidate ${N*st.mean(cb):.2f}/day")
print("  (the decision day is at least 7 and at least 200 samples; labels from the exact scorer)")
for label, reg in (("candidate as measured", 0.0), ("INJECTED regression A: candidate loses 25% of its right answers on template A, true overall change about -0.067 (SYNTHETIC)", 0.25), ("INJECTED regression B: loses 10% of its right answers on template A, true overall change about -0.017, inside the margin, so promote is the right decision (SYNTHETIC)", 0.10)):
    print(f" {label}")
    for seg in (False, True):
        for f in (0.01, 0.05, 0.10, 1.00):
            res = [program(f, s_, reg, seg) for s_ in range(300)]; dec = [r for r in res if r[1] != "undecided"]
            und = sum(1 for r in res if r[1] == "undecided") / len(res); pro = sum(1 for r in res if r[1] == "promote") / len(res); rej = sum(1 for r in res if r[1] == "reject") / len(res)
            days = sorted(r[0] for r in dec); med = days[len(days) // 2] if days else None
            spend = f * N * st.mean(cb) * (med if med else HORIZON); lab = f * N * (JUDGE or 0) * (med if med else HORIZON)
            print(f"   {'segment gate on' if seg else 'overall gate  '} f={f:4.0%}: promote {pro:.2f} reject {rej:.2f} undecided {und:.2f}; median decision day {med}; shadow inference ${spend:.2f}; judge labels ${lab:.2f}; total ${spend+lab:.2f}")
