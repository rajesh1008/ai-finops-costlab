#!/usr/bin/env python3
"""Summarise output_cap_lab: per model and cap, mean billed output, share stopped by the cap, share with no visible text."""
import json
from pathlib import Path
def summarise(rows):
    cells = {}
    for r in rows:
        if "error" in r: continue
        cells.setdefault((r["model"], r["cap"]), []).append(r)
    res = {}
    for (m, c), v in cells.items():
        n = len(v)
        res[(m, c)] = {"n": n, "mean_out": sum(x["out"] for x in v) / n,
                       "truncated": sum(x["stop"] == "max_tokens" for x in v) / n,
                       "no_visible": sum(x["visible_chars"] == 0 for x in v) / n}
    return res
if __name__ == "__main__":
    p = Path(__file__).resolve().parents[1] / "runs" / "output-cap-lab-2026-11-12.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    print("errors:", sum("error" in r for r in rows), "of", len(rows))
    for (m, c), s in sorted(summarise(rows).items()):
        print(m, "cap", c, "n", s["n"], "mean_out", round(s["mean_out"], 1), "truncated", round(s["truncated"], 3), "no_visible", round(s["no_visible"], 3))
