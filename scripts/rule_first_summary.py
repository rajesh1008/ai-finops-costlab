#!/usr/bin/env python3
"""Summarise the Chapter 16 rule-first lab. Prices are ASSUMED placeholders ($ per million input, output)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from rule_first_lab import rule, make
PRICE = {"m": (1.0, 5.0), "claude-haiku-4-5-20251001": (1.0, 5.0), "claude-haiku-5-5": (1.0, 5.0)}
def summarise(rows):
    out = {}
    for m in sorted({r["model"] for r in rows}):
        rs = [r for r in rows if r["model"] == m]; pi, po = PRICE[m]
        cost = lambda r: (r["in"] * pi + r["out"] * po) / 1e6
        ruled = [r for r in rs if rule(r["text"]) is not None]
        rule_ok = sum(rule(r["text"]) == r["truth"] for r in ruled)
        model_ok = sum(r["answer"] == r["truth"] for r in rs)
        hyb_ok = sum((rule(r["text"]) if rule(r["text"]) is not None else r["answer"]) == r["truth"] for r in rs)
        fall = [r for r in rs if rule(r["text"]) is None]
        out[m] = {"n": len(rs), "rule_handles": len(ruled), "rule_correct_of_handled": rule_ok, "model_only_correct": model_ok,
                  "hybrid_correct": hyb_ok, "model_only_cost": sum(map(cost, rs)), "hybrid_cost": sum(map(cost, fall)),
                  "model_wrong_on_rule_handled": sum(r["answer"] != r["truth"] for r in ruled),
                  "rule_wrong_formats": sorted({r["fmt"] for r in ruled if rule(r["text"]) != r["truth"]}),
                  "mean_out_tokens": sum(r["out"] for r in rs) / len(rs)}
    return out
if __name__ == "__main__":
    rows = [json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()]
    for m, s in summarise(rows).items(): print(m, json.dumps(s, indent=1))
