#!/usr/bin/env python3
"""Chapter 35 follow-up summary: B3 (thinking disabled plus an object-only instruction) against B0 and B1 of the main lab, under the fence-stripping shim, with the template C breakdown. Prices are the dated placeholders."""
import json, statistics
from collections import Counter
from pathlib import Path
from costlab.modelchange import classify, call_cost, GOOD
R = Path(__file__).resolve().parents[1] / "runs"
def block(name, d, arm, model):
    Q = d["questions"]; rs = [r for r in d["results"] if r["arm"] == arm and not r["error"]]
    cl = [classify(r["text"], Q[r["q"]]["gold"], Q[r["q"]]["answerable"], True) for r in rs]; cnt = Counter(cl); n = len(rs)
    cost = sum(call_cost(model, r["in"], r["out"]) for r in rs); good = sum(c in GOOD for c in cl)
    c_rows = [(r, c) for r, c in zip(rs, cl) if Q[r["q"]]["t"] == "C"]; cg = sum(c in GOOD for _, c in c_rows)
    print(f"{name}: n={n} good {good} ({good/n*100:.1f}%) correct {cnt['correct']} correct_decline {cnt['correct_decline']} wrong {cnt['wrong']} wrong_decline {cnt['wrong_decline']} unparsed {cnt['unparsed']}; template C good {cg}/{len(c_rows)}; mean out {statistics.mean(r['out'] for r in rs):.1f}; $/1000 calls {cost/n*1000:.4f}; $/1000 good {cost/max(1,good)*1000:.4f}")
def main():
    m = json.load(open(R / "model-change-lab-2026-11-11.json")); f = json.load(open(R / "model-change-followup-2026-11-11.json"))
    B = "claude-haiku-5-5"
    assert [q["q"] for q in f["questions"]] == [q["q"] for q in m["questions"]]; f["questions"] = m["questions"]  # the main lab holds the answerable flags
    print("calls in follow-up", len(f["results"]), "errors", sum(1 for r in f["results"] if r["error"]))
    block("B0 default thinking", m, "B0", B); block("B1 thinking off", m, "B1", B); block("B3 thinking off + object-only instruction", f, "B3", B)
if __name__ == "__main__": main()
