"""Keyless lab (mode: simulated). Cache TTL gap economics from published Anthropic list prices. No model is called.

Assumptions (stated, not measured): 20,000-token shared prefix, 300-token question, 400-token answer, 100 calls
at a steady gap between calls. Compares no caching, 5-minute TTL and 1-hour TTL (a read refreshes the entry).
Output: runs/simulated/cache-gap-economics-<date>.json and .txt
"""
import argparse, datetime, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from costlab.backends import simulated

GAPS = [0.5, 2, 4, 5, 6, 10, 30, 59, 61, 120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-haiku-4-5")
    a = ap.parse_args()
    rows = simulated.breakeven_gap_table(a.model, GAPS, prefix_tokens=20_000, suffix_tokens=300, output_tokens=400, calls=100)
    today = datetime.date.today().isoformat()
    out = {**simulated.provenance(a.model), "lab": "cache TTL gap economics", "run_date": today,
           "assumptions": {"prefix_tokens": 20_000, "question_tokens": 300, "answer_tokens": 400, "calls": 100},
           "rows": rows}
    d = pathlib.Path(__file__).resolve().parents[1] / "runs" / "simulated"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"cache-gap-economics-{today}.json").write_text(json.dumps(out, indent=2))
    lines = [f"mode: simulated | priced as: {a.model} list prices dated {out['pricing_date']} ({out['pricing_source']})",
             out["note"], "Assumed: 20,000-token prefix, 300-token question, 400-token answer, 100 calls at a steady gap.", "",
             f"{'gap (min)':>9} {'no cache $':>11} {'5m TTL $':>10} {'1h TTL $':>10}  cheapest"]
    for r in rows:
        lines.append(f"{r['gap_min']:>9} {r['none']:>11.4f} {r['5m']:>10.4f} {r['1h']:>10.4f}  {r['cheapest']}")
    (d / f"cache-gap-economics-{today}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
