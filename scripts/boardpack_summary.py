#!/usr/bin/env python3
"""Chapter 40 summary: from the 400 real calls, compute the four ways a board line can describe the same two models, loaded cost per outcome with bootstrap ranges, and a three-quarter pack with ASSUMED volumes and revenue."""
import json, sys
from pathlib import Path
from costlab.boardpack import *
RUN = Path(__file__).resolve().parents[1] / "runs" / "boardpack-lab-2026-11-11.json"
MOD = {"M1": "claude-haiku-4-5-20251001", "M2": "claude-haiku-5-5", "M2x": "claude-haiku-5-5"}
R = json.load(open(RUN))["results"] + json.load(open(RUN.parent / "boardpack-fix-lab-2026-11-11.json"))["results"]
out = []
def p(s=""): print(s); out.append(s)
by = {m: sorted([r for r in R if r["m"] == m], key=lambda r: r["i"]) for m in MOD}
p(f"calls {len(R)} errors {sum(1 for r in R if r['error'])}")
stat = {}
for m, rows in by.items():
    cls = [classify(r["text"], r["ok"]) for r in rows]; inf = [call_usd(MOD[m], r["in"], r["out"]) for r in rows]
    b = loaded_cost(cls, inf); stat[m] = (cls, inf, b)
    p(f"{m} {MOD[m]}: in median {sorted(r['in'] for r in rows)[len(rows)//2]} out median {sorted(r['out'] for r in rows)[len(rows)//2]} | list blended $/Mtok {list_price_per_mtok(MOD[m]):.3f} | cost per call ${sum(inf)/len(inf):.6f} | correct {b['correct']} decline {b['declines']} wrong {b['wrongs']} of {b['n']}")
    p(f"   inference per correct answer ${cost_per_correct_only(b):.6f} | loaded cost per closed ticket ${cost_per_outcome(b):.4f} (inference {b['inference']/b['n']:.6f}, platform {b['platform']/b['n']:.4f}, human {b['human']/b['n']:.4f}, rework {b['rework']/b['n']:.4f})")
    lo, hi = bootstrap_ci(lambda idx: loaded_cost([cls[i] for i in idx], [inf[i] for i in idx])["total"] / len(idx), len(rows))
    p(f"   loaded cost per closed ticket 95% bootstrap range ${lo:.4f} to ${hi:.4f}")
    for t in "ABC":
        ix = [i for i, r in enumerate(rows) if r["t"] == t]
        bb = loaded_cost([cls[i] for i in ix], [inf[i] for i in ix])
        p(f"   template {t}: n {len(ix)} correct {bb['correct']} decline {bb['declines']} wrong {bb['wrongs']} loaded ${cost_per_outcome(bb):.4f}")
a, b2 = stat["M1"], stat["M2"]
p()
p("Same change, four board metrics (M1 -> M2):")
p(f"  list price per token: {list_price_per_mtok(MOD['M1'])/list_price_per_mtok(MOD['M2']):.1f}x lower")
p(f"  inference cost per call: {(sum(a[1])/len(a[1]))/(sum(b2[1])/len(b2[1])):.2f}x lower")
p(f"  inference cost per correct answer: {cost_per_correct_only(a[2])/cost_per_correct_only(b2[2]):.2f}x lower")
p(f"  loaded cost per closed ticket: {cost_per_outcome(a[2])/cost_per_outcome(b2[2]):.2f}x ({'lower' if cost_per_outcome(a[2])>cost_per_outcome(b2[2]) else 'higher'} for M2)")
p()
REV = 4.00
p("Margin per closed ticket at ASSUMED revenue $%.2f, human $6.00, rework $4.00, platform $0.004 per call:" % REV)
for m in MOD: p(f"  {m}: margin {margin(REV, cost_per_outcome(stat[m][2]))*100:.1f}%")
p()
p("Four-quarter pack, ASSUMED volumes (tickets per quarter), M1 in Q1, M2 in Q2 and Q3, M2 with expanded retrieval (M2x) in Q4:")
vol = {"Q1": 150000, "Q2": 210000, "Q3": 300000, "Q4": 360000}
prev = None
for q, mm in (("Q1", "M1"), ("Q2", "M2"), ("Q3", "M2"), ("Q4", "M2x")):
    c = cost_per_outcome(stat[mm][2]); mg = margin(REV, c); dec = decision(mg, prev if prev is not None else mg)
    p(f"  {q} {mm}: tickets {vol[q]:,} loaded cost per ticket ${c:.4f} margin {mg*100:.1f}% total cost ${c*vol[q]:,.0f} decision {dec}"); prev = mg
base_h = 6.0
p(f"  baseline cost per ticket without AI (ASSUMED all-human): ${base_h:.2f}")
for q, mm in (("Q1", "M1"), ("Q2", "M2"), ("Q3", "M2"), ("Q4", "M2x")):
    c = cost_per_outcome(stat[mm][2]); p(f"  {q} net contribution vs all-human, measured unit cost times assumed volume: ${(base_h-c)*vol[q]:,.0f}")
# what the failure terms are worth: sensitivity of cost per ticket to the human and rework assumptions
p()
p("Sensitivity of loaded cost per ticket to the ASSUMED human cost and rework cost (M2):")
cls, inf, _ = stat["M2"]
for h in (3.0, 6.0, 12.0):
    row = []
    for rw in (0.0, 4.0, 12.0): row.append(f"${cost_per_outcome(loaded_cost(cls, inf, human=h, rework=rw)):.3f}")
    p(f"  human ${h:.0f}: rework $0 / $4 / $12 -> " + " / ".join(row))
p()
p("Break-even failure share: the share of tickets that must end in a person's hands (any cost) for the AI path to match all-human at $6.00:")
for m in MOD:
    cls, inf, _ = stat[m]; infm = sum(inf)/len(inf)
    # AI cost per ticket = infm + 0.004 + f*6 ; equals 6 when f = (6-infm-0.004)/6
    p(f"  {m}: mean inference ${infm:.6f}; break-even handoff share {(6.0-infm-0.004)/6.0*100:.1f}% (measured handoff share {(stat[m][2]['declines']+stat[m][2]['wrongs'])/stat[m][2]['n']*100:.1f}%)")
Path(RUN.parent / "boardpack-summary-2026-11-11.txt").write_text("\n".join(out) + "\n")
