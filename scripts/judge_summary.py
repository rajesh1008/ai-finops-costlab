#!/usr/bin/env python3
"""Chapter 29: arithmetic over judge-lab-2026-11-10.json and shadow-lab-2026-11-10.json (no API). Rates haiku-4-5 $1/$5, haiku-5-5 $0.10/$0.50 per M (placeholder).
Part 1 each judge against the exact scorer on 450 items (300 recorded incumbent answers + 150 SYNTHETIC corruptions). Part 2 what the judge costs next to the thing it judges. Part 3 estimating accuracy from judge labels plus a small gold set (prediction-powered), against gold only.
Part 4 a SYNTHETIC monthly evaluation bill."""
import json, random, statistics as st, math
from pathlib import Path
from costlab.ladder import usd, wilson, ppi_mean, normal_ci
RUNS = Path(__file__).resolve().parents[1] / "runs"
j = json.load(open(RUNS / "judge-lab-2026-11-10.json")); sh = json.load(open(RUNS / "shadow-lab-2026-11-10.json")); items = j["items"]; Qs = sh["questions"]
RATE = {"ctx_h5": (0.10, 0.50), "ref_h5": (0.10, 0.50), "cot_h5": (0.10, 0.50), "think_h5": (0.10, 0.50), "ctx_h4": (1.0, 5.0)}
inc = [r for r in sh["results"] if r["model"] == sh["models"]["incumbent"]]; gen_cost = st.mean(usd(r["in"], r["out"], (1.0, 5.0)) for r in inc)
print(f"items {len(items)} (recorded {sum(1 for i in items if i['kind']=='recorded')}, corrupted {sum(1 for i in items if i['kind']=='corrupted')}); gold-correct {sum(i['gold_ok'] for i in items)}; mean cost of generating one incumbent answer ${gen_cost:.6f} (haiku-4-5, one call)")
V = {n: {} for n in RATE}
for r in j["results"]: V[r["judge"]][r["item"]] = r
print("\nPart 1: judge verdict against the exact scorer (positive = answer is correct)")
J = {}
for n in RATE:
    tp = fp = tn = fn = nv = 0; costs = []; outs = []; vv = []
    for k, it in enumerate(items):
        r = V[n][k]; costs.append(usd(r["in"], r["out"], RATE[n])); outs.append(r["out"])
        if r["verdict"] is None: nv += 1; vv.append(None); continue
        v = r["verdict"] == "CORRECT"; vv.append(int(v))
        if it["gold_ok"] and v: tp += 1
        elif it["gold_ok"] and not v: fn += 1
        elif not it["gold_ok"] and v: fp += 1
        else: tn += 1
    J[n] = vv; dn = tp + fp + tn + fn
    print(f"  {n:7s}: agree {(tp+tn)/dn:.3f} of {dn} ({nv} no verdict); catches wrong answers (TNR) {tn}/{tn+fp} = {tn/max(tn+fp,1):.3f}; passes right answers (TPR) {tp}/{tp+fn} = {tp/max(tp+fn,1):.3f}; mean cost ${st.mean(costs):.6f}/judgement; mean output {st.mean(outs):.1f} tokens; cost / generation cost {st.mean(costs)/gen_cost:.2f}")
print("  wrong answers split: recorded wrong (almost all are 'cannot answer' declines) vs SYNTHETIC corruptions; share the judge calls INCORRECT")
for n in RATE:
    rw = [k for k, it in enumerate(items) if it["kind"] == "recorded" and not it["gold_ok"] and J[n][k] is not None]; cw = [k for k, it in enumerate(items) if it["kind"] == "corrupted" and not it["gold_ok"] and J[n][k] is not None]
    print(f"  {n:8s}: recorded-wrong caught {sum(1 for k in rw if J[n][k]==0)}/{len(rw)}; corruptions caught {sum(1 for k in cw if J[n][k]==0)}/{len(cw)}")
rt = [k for k, it in enumerate(items) if it["kind"] == "recorded" and it["gold_ok"]]
print("  judge disagreement with scorer on right answers, by question type (ref_h5):", {t: sum(1 for k in rt if Qs[items[k]["q"]]["t"] == t and J["ref_h5"][k] == 0) for t in "AB"})
print("\nPart 3: estimating the incumbent's accuracy on the 450 items (true value by scorer =", f"{sum(i['gold_ok'] for i in items)/len(items):.3f}) using the ctx_h5 judge on all items and m gold labels, 2,000 resamples")
vals = J["ctx_h5"]; usable = [k for k in range(len(items)) if vals[k] is not None]; truth = sum(items[k]["gold_ok"] for k in usable) / len(usable)
print(f"  naive judge mean (all {len(usable)} usable): {sum(vals[k] for k in usable)/len(usable):.3f} (bias {sum(vals[k] for k in usable)/len(usable)-truth:+.3f})")
rnd = random.Random(293)
for m in (20, 50, 100):
    cov_p = cov_g = 0; w_p = []; w_g = []; err_p = []
    for _ in range(2000):
        cal = rnd.sample(usable, m); rest = [k for k in usable if k not in set(cal)]
        e, se = ppi_mean([vals[k] for k in rest], [vals[k] for k in cal], [int(items[k]["gold_ok"]) for k in cal]); lo, hi = normal_ci(e, se)
        cov_p += lo <= truth <= hi; w_p.append(hi - lo); err_p.append(e - truth)
        g = sum(items[k]["gold_ok"] for k in cal) / m; gse = math.sqrt(max(g * (1 - g), 0.0025) / m); cov_g += g - 1.96 * gse <= truth <= g + 1.96 * gse; w_g.append(2 * 1.96 * gse)
    print(f"  m={m:3d} gold labels: gold-only CI width {st.mean(w_g):.3f} (coverage {cov_g/2000:.2f}); judge+gold (PPI) CI width {st.mean(w_p):.3f} (coverage {cov_p/2000:.2f}, mean error {st.mean(err_p):+.4f})")
print("\nPart 4: SYNTHETIC monthly evaluation bill (ILLUSTRATIVE volumes; measured per-call costs above)")
prod = 3000 * 30 * gen_cost
print(f"  production inference at 3,000 requests/day, incumbent: ${prod:.2f}/month")
sj = st.mean(usd(V['ctx_h5'][k]['in'], V['ctx_h5'][k]['out'], RATE['ctx_h5']) for k in range(len(items))); cj = st.mean(usd(V['cot_h5'][k]['in'], V['cot_h5'][k]['out'], RATE['cot_h5']) for k in range(len(items))); tj = st.mean(usd(V['think_h5'][k]['in'], V['think_h5'][k]['out'], RATE['think_h5']) for k in range(len(items))); hj = st.mean(usd(V['ctx_h4'][k]['in'], V['ctx_h4'][k]['out'], RATE['ctx_h4']) for k in range(len(items)))
for label, per in (("verdict-only judge, haiku-5-5", sj), ("verdict-only judge, haiku-5-5, thinking left on", tj), ("explain-then-verdict judge, haiku-5-5", cj), ("verdict-only judge, haiku-4-5", hj)):
    reg = 20 * 300 * per; online = 0.05 * 3000 * 30 * per; trip = 20 * 300 * 3 * per
    print(f"  {label}: regression suite 300 items x 20 releases = ${reg:.2f}; same x3 repeats = ${trip:.2f}; online 5% sample = ${online:.2f}; online 100% = ${3000*30*per:.2f} ({3000*30*per/prod:.2f} x production inference)")
