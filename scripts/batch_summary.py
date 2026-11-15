#!/usr/bin/env python3
"""Chapter 20: summarise the recorded batch lab (no API call). Cost = placeholder table times the batch factor 0.5 (vendor page)."""
import json, sys
from pathlib import Path
from costlab.estimate import estimate_usd
from costlab.cascade import make_problems, correct
RUNS = Path(__file__).resolve().parents[1] / "runs"
def summarise(path):
    d = json.load(open(path)); probs = {f"bill-{p['id']}": p for p in make_problems()}; out = {}
    for name, b in d["batches"].items():
        ok = [r for r in b["rows"] if "in" in r]
        sync = sum(estimate_usd("anthropic:" + b["model"], r["in"], r["out"], r["cr"], r["cw"]) for r in ok)
        if name == "handbook": sync += sum(r["cw"] for r in ok) * (2.0 - 1.25) * 1.00 / 1e6   # the lab asked for the 1-hour tier: write at 2x input, table holds 1.25x
        row = {"model": b["model"], "seconds_to_end": b["seconds_to_end"], "succeeded": len(ok), "of": len(b["rows"]),
               "sync_estimate_usd": round(sync, 5), "batch_estimate_usd": round(sync * 0.5, 5),
               "cache_read_tokens": sum(r["cr"] for r in ok), "cache_write_tokens": sum(r["cw"] for r in ok),
               "requests_with_read": sum(1 for r in ok if r["cr"] > 0)}
        if name == "billing": row["correct"] = sum(1 for r in ok if correct(r["text"], probs[r["id"]]["answer"]))
        out[name] = row
    return out
if __name__ == "__main__":
    s = summarise(RUNS / "batch-lab-2026-11-10.json")
    text = json.dumps(s, indent=1); print(text); (RUNS / "batch_summary-2026-11-10.txt").write_text(text + "\n")
