#!/usr/bin/env python3
"""Chapter 31: re-reads portability-schema-2026-11-11.json with a strict parser (whole reply is JSON) and a lenient parser (strips one code fence). Arithmetic only."""
import json, re, statistics
from pathlib import Path
from costlab.estimate import estimate_usd
R = Path(__file__).resolve().parents[1] / "runs"
def lenient(t):
    t = t.strip(); m = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", t, re.S)
    return json.loads(m.group(1) if m else t)
def main():
    d = json.load(open(R / "portability-schema-2026-11-11.json")); Q = d["questions"]
    for m in sorted({r["model"] for r in d["results"]}):
        rr = [r for r in d["results"] if r["model"] == m]; strict = sum(r["parsed"] for r in rr); ok = dec = wrong = fence = bad = 0; declinesC = 0
        for r in rr:
            try: o = lenient(r["text"])
            except Exception: bad += 1; continue
            fence += r["text"].lstrip().startswith("```")
            vals = [str(o.get("ref")), str(o.get("days"))]; g = Q[r["q"]]["gold"]
            if o.get("answerable") is False: dec += 1; declinesC += Q[r["q"]]["t"] == "C"
            elif all(x in vals for x in g): ok += 1
            else: wrong += 1
        c = statistics.mean(estimate_usd("anthropic:" + m, r["in"], r["out"]) for r in rr) * 1000
        print(f"{m:<28} strict-parsed {strict}/60  fenced {fence}  lenient: correct {ok} declined {dec} (on type C {declinesC}) confident-wrong {wrong} still-unparsed {bad}  $/1000 {c:.4f}")
if __name__ == "__main__": main()
