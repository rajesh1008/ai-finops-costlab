#!/usr/bin/env python3
"""Chapter 11 offline summary of cpo-repeats-lab. How wide is the interval on cost per correct answer as the number of items grows? Resamples ITEMS (with their repeats) 4000 times, seed 11. Placeholder prices from costlab.prices."""
import json, random
from pathlib import Path
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
RUNS = Path(__file__).resolve().parents[1] / "runs"
def cost(x):
    p = P["anthropic:" + x["model"]]; return (x["in"] * p["input"] + x["out"] * p["output"]) / 1e6
def cpc(rows):
    c = sum(r["correct"] for r in rows)
    return sum(cost(r) for r in rows) / c if c else float("inf")
def interval(by_item, n, reps=4000, seed=11):
    r = random.Random(seed); keys = list(by_item); vals = []
    for _ in range(reps):
        rows = [y for k in (r.choice(keys) for _ in range(n)) for y in by_item[k]]
        vals.append(cpc(rows))
    vals.sort(); return vals[int(0.05 * reps)], vals[int(0.5 * reps)], vals[int(0.95 * reps)]
def main():
    rows = [json.loads(l) for l in (RUNS / "cpo-repeats-lab-2026-11-11.jsonl").read_text().splitlines()]
    out = []
    for m in sorted({r["model"] for r in rows}):
        q = [r for r in rows if r["model"] == m]; by = {}
        for r in q: by.setdefault(r["item"], []).append(r)
        per_item = [sum(y["correct"] for y in v) for v in by.values()]
        out.append(f"{m}: calls {len(q)} correct {sum(r['correct'] for r in q)} cost ${sum(cost(r) for r in q):.4f} cost per correct ${cpc(q):.5f}")
        out.append(f"  items 3 of 3 correct {per_item.count(3)}, 2 of 3 {per_item.count(2)}, 1 of 3 {per_item.count(1)}, 0 of 3 {per_item.count(0)}")
        for n in (5, 10, 20, 40):
            lo, md, hi = interval(by, n)
            out.append(f"  resample {n:2d} items (x3 repeats): cost per correct 5th ${lo:.5f}  median ${md:.5f}  95th ${hi:.5f}  width/median {(hi-lo)/md:.2f}")
    s = "\n".join(out); print(s); (RUNS / "cpo-repeats-summary-2026-11-11.txt").write_text(s + "\n")
if __name__ == "__main__": main()
