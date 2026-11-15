#!/usr/bin/env python3
"""Ch9 / Ch18 (51st run). Find cache-write bursts: two or more calls with the same prefix that both WROTE the cache
and started within WINDOW seconds of each other. Reads the stagger-lab JSONL files (each chain = one prefix).
Usage: python scripts/cache_write_burst.py runs/cache-substagger-lab-2026-11-15.jsonl [window_s]"""
import sys, json
from pathlib import Path
def bursts(rows, window=0.25):
    out = []
    for r in rows:
        w = sorted(u["start_s"] for u in r["rows"] if "error" not in u and u["cw"] > 0)
        n = sum(1 for a, b in zip(w, w[1:]) if b - a <= window)
        if n: out.append({"gap": r["gap"], "rep": r["rep"], "writes": len(w), "close_pairs": n})
    return out
def wasted_premium(rows, in_rate=1.00, write_mult=1.25):
    """Extra cost of the writes beyond the first in each chain, over reading: (write - read) price on those tokens, USD."""
    t = 0.0
    for r in rows:
        ws = [u for u in r["rows"] if "error" not in u and u["cw"] > 0][1:]
        t += sum(u["cw"] * in_rate * (write_mult - 0.10) / 1e6 for u in ws)
    return t
def main(p, window):
    rows = [json.loads(l) for l in Path(p).read_text().splitlines()]
    b = bursts(rows, window)
    print(f"{len(rows)} chains, {len(b)} with a write burst (window {window}s)")
    for x in b: print(x)
    print(f"extra spend on repeat writes: ${wasted_premium(rows):.4f}")
if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.25)
