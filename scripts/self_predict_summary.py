#!/usr/bin/env python3
"""Summarise self_predict_lab output: ratio of predicted to actual billed output tokens, direction, rank correlation."""
import json, sys, statistics as st
from pathlib import Path
from scipy.stats import spearmanr
F = Path(__file__).resolve().parents[1] / "runs" / "self-predict-lab-2026-11-12.jsonl"
def summarise(rows):
    out = {}
    for m in sorted({r["model"] for r in rows}):
        q = [r for r in rows if r["model"] == m and r["pred"]]
        ratios = [r["pred"] / r["actual"] for r in q]
        under = sum(r["pred"] < r["actual"] for r in q)
        rho = spearmanr([r["pred"] for r in q], [r["actual"] for r in q]).correlation
        out[m] = {"n": len(q), "unparsed": sum(1 for r in rows if r["model"] == m and not r["pred"]), "median_ratio": round(st.median(ratios), 2), "under": under, "within_2x": sum(0.5 <= x <= 2 for x in ratios), "spearman": round(float(rho), 2), "mean_pred": round(st.mean(r["pred"] for r in q)), "mean_actual": round(st.mean(r["actual"] for r in q)), "mean_pred_call_out": round(st.mean(r["pred_call_out"] for r in q))}
    return out
if __name__ == "__main__":
    rows = [json.loads(l) for l in F.read_text().splitlines()]
    s = summarise(rows)
    for m, v in s.items(): print(m, v)
    by = {}
    for r in rows:
        if r["pred"]: by.setdefault((r["model"][7:16], r["kind"]), []).append((r["pred"], r["actual"]))
    for k, v in sorted(by.items()): print(k, "pred %.0f actual %.0f" % (st.mean(a for a, _ in v), st.mean(b for _, b in v)))
