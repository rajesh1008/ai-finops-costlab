#!/usr/bin/env python3
"""Chapter 41 summary: agreement with the author's labels, inflation rate on decoys, per model and prompt; plus the score arithmetic and the gaming example."""
import json, re
from pathlib import Path
from collections import Counter, defaultdict
from costlab.maturity import *
RUN = Path(__file__).resolve().parents[1] / "runs" / "maturity-lab-2026-11-11.json"
R = json.load(open(RUN))["results"]; out = []
def p(s=""): print(s); out.append(s)
def parse(t):
    m = re.search(r'"level"\s*:\s*"(crawl|walk|run)"', t, re.I)
    return LEVELS.index(m.group(1).lower()) if m else None
p(f"calls {len(R)} errors {sum(1 for r in R if r['error'])} unparsed {sum(1 for r in R if parse(r['text']) is None)}")
cell = defaultdict(list)
for r in R:
    s = STATEMENTS[r["i"]]; lv = parse(r["text"]); cell[(r["m"], r["mode"])].append((s, lv))
for (m, mode), xs in sorted(cell.items()):
    n = len(xs); ok = sum(1 for s, lv in xs if lv == s["true"])
    plain = [(s, lv) for s, lv in xs if s["kind"] == "plain"]; dec = [(s, lv) for s, lv in xs if s["kind"] == "decoy"]
    infl = sum(1 for s, lv in dec if lv is not None and lv > s["true"]); defl = sum(1 for s, lv in xs if lv is not None and lv < s["true"])
    p(f"{m} prompt {mode}: exact {ok}/{n} ({ok/n*100:.1f}%) | plain {sum(1 for s,lv in plain if lv==s['true'])}/{len(plain)} | decoys exact {sum(1 for s,lv in dec if lv==s['true'])}/{len(dec)}, inflated {infl}/{len(dec)} | deflated overall {defl} | unparsed {sum(1 for s,lv in xs if lv is None)}")
# confusion for G vs F pooled over models, decoys
for mode in "FG":
    c = Counter()
    for m in ("h45", "h55"):
        for s, lv in cell[(m, mode)]:
            if s["kind"] == "decoy": c[(s["true"], lv)] += 1
    p(f"decoys prompt {mode}, (true, judged) counts pooled over both models: " + ", ".join(f"{LEVELS[a]}->{LEVELS[b] if b is not None else 'none'}:{n}" for (a, b), n in sorted(c.items(), key=lambda kv: (kv[0][0], -1 if kv[0][1] is None else kv[0][1]))))
# which decoys fooled most
fool = Counter()
for (m, mode), xs in cell.items():
    for s, lv in xs:
        if mode == "F" and s["kind"] == "decoy" and lv is not None and lv > s["true"]: fool[s["text"][:70]] += 1
p("decoys inflated under F by most runs (max 2 models):")
for t, n in fool.most_common(6): p(f"  {n}: {t}")
# score arithmetic: author labels as a team's shown levels vs a self-assessment from the inflated F readings
shown = {c: 0 for c in CAPS}
p()
p("Score arithmetic (equal weights): a team at walk on all eight capabilities scores %.1f; run on all eight %.1f; walk on four and crawl on four %.1f." % (score({c: 1 for c in CAPS}), score({c: 2 for c in CAPS}), score({c: (1 if i < 4 else 0) for i, c in enumerate(CAPS)})))
fs = {"allocation": 1, "metering": 1, "unit_economics": 0, "forecasting": 1, "anomaly": 1, "budgets": 0, "commitments": 0, "governance": 1}   # author-composed Fieldstone, shown artefacts (Q4 start)
p("Fieldstone (composed, author-assigned) levels: " + ", ".join(f"{c} {LEVELS[v]}" for c, v in fs.items()) + f" -> score {score(fs):.1f}; weakest: {', '.join(weakest(fs))}")
g = gaming_example(); p(f"Gaming example: coverage {g['coverage_before']*100:.0f}% -> {g['coverage_after_dumping_into_shared']*100:.0f}% by dumping 62 of 100 dollars into a shared bucket; owned spend share stays {g['owned_spend_share_after']*100:.0f}%")
Path(RUN.parent / "maturity-summary-2026-11-11.txt").write_text("\n".join(out) + "\n")
