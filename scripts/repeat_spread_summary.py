#!/usr/bin/env python3
"""Summarise repeat_spread_lab output: per model, per prompt, mean, coefficient of variation and max/min of billed output tokens."""
import json, sys, statistics as st
from pathlib import Path
def summarise(rows):
    out = {}
    cells = {}
    for r in rows:
        if "error" in r: continue
        cells.setdefault((r["model"], r["kind"], r["p"]), []).append(r["out"])
    for (m, k, p), v in cells.items():
        mean = st.mean(v); sd = st.pstdev(v)
        out.setdefault(m, []).append({"kind": k, "p": p, "n": len(v), "mean": mean, "cv": (sd / mean if mean else 0.0), "ratio": (max(v) / min(v) if min(v) else None)})
    res = {}
    for m, cs in out.items():
        cvs = sorted(c["cv"] for c in cs); rat = sorted(c["ratio"] for c in cs if c["ratio"])
        res[m] = {"cells": len(cs), "median_cv": st.median(cvs), "max_cv": cvs[-1], "median_ratio": st.median(rat), "max_ratio": rat[-1], "cells_by_cv": sorted(cs, key=lambda c: -c["cv"])}
    return res
if __name__ == "__main__":
    p = Path(__file__).resolve().parents[1] / "runs" / "repeat-spread-lab-2026-11-12.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    print("errors:", sum("error" in r for r in rows), "of", len(rows))
    for m, s in summarise(rows).items():
        print(m, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items() if k != "cells_by_cv"})
        for c in s["cells_by_cv"]: print("  ", c["kind"], c["p"], "n", c["n"], "mean", round(c["mean"]), "cv", round(c["cv"], 3), "max/min", round(c["ratio"], 2) if c["ratio"] else None)
