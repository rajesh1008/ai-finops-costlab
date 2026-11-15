"""Keyless lab (mode: simulated). Which cache TTL wins when traffic is bursty? No model is called.

Assumptions (stated, not measured): 20,000-token prefix, 300-token question, 400-token answer, 200 calls, priced as
claude-haiku-4-5 list prices. Gaps are drawn from a seeded two-state mix: a 'burst' gap (uniform 0.2-2 min) and an 'idle'
gap whose length is uniform in a stated range. The idle share is swept from 0 to 50 percent of gaps.
Output: runs/simulated/bursty-ttl-<date>.json and .txt
"""
import datetime, json, pathlib, random, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from costlab.backends import simulated

MODEL = "claude-haiku-4-5"
SHARES = [0.0, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50]
IDLE_RANGES = {"short idle (6-30 min)": (6, 30), "long idle (6-240 min)": (6, 240)}
CALLS, TRIALS = 200, 200


def gaps(share, lo, hi, rng):
    return [rng.uniform(lo, hi) if rng.random() < share else rng.uniform(0.2, 2.0) for _ in range(CALLS - 1)]


def run():
    rows = []
    for label, (lo, hi) in IDLE_RANGES.items():
        for s in SHARES:
            rng = random.Random(1000 + int(s * 1000))
            tot = {"none": 0.0, "5m": 0.0, "1h": 0.0}
            for _ in range(TRIALS):
                g = gaps(s, lo, hi, rng)
                for name, ttl in (("none", None), ("5m", "5m"), ("1h", "1h")):
                    tot[name] += simulated.simulate_session(MODEL, g, prefix_tokens=20_000, suffix_tokens=300,
                                                            output_tokens=400, ttl=ttl)["total_usd"]
            m = {k: v / TRIALS for k, v in tot.items()}
            rows.append({"idle_range": label, "idle_share": s, **m, "cheapest": min(m, key=m.get)})
    return rows


def main():
    rows = run()
    today = datetime.date.today().isoformat()
    out = {**simulated.provenance(MODEL), "lab": "bursty traffic TTL choice", "run_date": today,
           "assumptions": {"prefix": 20000, "question": 300, "answer": 400, "calls": CALLS, "trials": TRIALS, "burst_gap_min": [0.2, 2.0]},
           "rows": rows}
    d = pathlib.Path(__file__).resolve().parents[1] / "runs" / "simulated"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"bursty-ttl-{today}.json").write_text(json.dumps(out, indent=2))
    lines = [f"mode: simulated | priced as: {MODEL} list prices dated {out['pricing_date']}", out["note"],
             "Assumed: 20,000-token prefix, 300 question, 400 answer, 200 calls, mean of 200 seeded trials.", ""]
    for label in IDLE_RANGES:
        lines.append(label)
        lines.append(f"{'idle share':>10} {'no cache $':>11} {'5m $':>9} {'1h $':>9}  cheapest")
        for r in rows:
            if r["idle_range"] == label:
                lines.append(f"{r['idle_share']:>10.2f} {r['none']:>11.3f} {r['5m']:>9.3f} {r['1h']:>9.3f}  {r['cheapest']}")
        lines.append("")
    (d / f"bursty-ttl-{today}.txt").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
