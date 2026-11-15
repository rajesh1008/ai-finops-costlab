#!/usr/bin/env python3
"""Chapter 41 follow-up summary (prompt G2): agreement with the author's labels, inflation rate on decoys, per model and prompt; plus the score arithmetic and the gaming example."""
import json, re
from pathlib import Path
from collections import Counter, defaultdict
from costlab.maturity import *
RUN = Path(__file__).resolve().parents[1] / "runs" / "maturity-lab-g2-2026-11-11.json"
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

open(str(Path(__file__).resolve().parents[1] / 'runs' / 'maturity-g2-summary-2026-11-11.txt'),'w').write(chr(10).join(out)+chr(10))
