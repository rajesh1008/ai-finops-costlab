#!/usr/bin/env python3
"""Chapter 20 summary of runs/batch-scale-lab-2026-11-11.json: batch wall time by size from the API's own timestamps, price against the synchronous run of the same 100 requests, accuracy, tokens.
Prices are the dated placeholders; the batch factor 0.5 is from the vendor page opened on 10 November 2026."""
import json, statistics
from datetime import datetime
from pathlib import Path
from costlab.ladder import score
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
R = Path(__file__).resolve().parents[1] / "runs"
def main():
    d = json.load(open(R / "batch-scale-lab-2026-11-11.json")); Q = d["questions"]; t = P["anthropic:" + d["model"]]
    cost = lambda rows, f=1.0: sum((r["in"] * t["input"] + r["out"] * t["output"]) / 1e6 * f for r in rows if "in" in r)
    sy = d["sync"]; print(f"sync: 100 requests, {d['sync_secs']} s wall with 6 workers, cost ${cost(sy):.5f}, correct {sum(score(r['text'], Q[int(r['id'][1:])]['gold']) for r in sy)}/100, mean in {statistics.mean(r['in'] for r in sy):.1f} out {statistics.mean(r['out'] for r in sy):.1f}")
    for n, b in d["batches"].items():
        rows = [r for r in b["rows"] if "in" in r]; ca, en = datetime.fromisoformat(b["created_at"]), datetime.fromisoformat(b["ended_at"]) if b["ended_at"] else None
        secs = (en - ca).total_seconds() if en else None
        ok = sum(score(r["text"], Q[int(r["id"][1:])]["gold"]) for r in rows)
        print(f"batch {n:>3}: status {b['status']} counts {b['counts']} wall {secs} s; cost at 0.5x ${cost(rows, 0.5):.5f} (sync price ${cost(rows):.5f}); correct {ok}/{len(rows)}; mean in {statistics.mean(r['in'] for r in rows):.1f} out {statistics.mean(r['out'] for r in rows):.1f}")
    b100 = {r["id"]: r for r in d["batches"]["100"]["rows"] if "in" in r}; same = sum(1 for r in sy if r["id"] in b100 and r["text"].strip() == b100[r["id"]]["text"].strip())
    print(f"identical text between sync and batch on the same 100 requests: {same}/100; tokens identical: {sum(1 for r in sy if r['id'] in b100 and r['in']==b100[r['id']]['in'] and r['out']==b100[r['id']]['out'])}/100")
if __name__ == "__main__": main()
