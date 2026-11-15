#!/usr/bin/env python3
"""Chapter 31: summary of portability-lab (real calls) with the arithmetic of what each contract costs on each model. Placeholder rates."""
import json, statistics
from pathlib import Path
from costlab.estimate import estimate_usd
R = Path(__file__).resolve().parents[1] / "runs"
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** .5) / d
    return c - h, c + h
def main():
    d = json.load(open(R / "portability-lab-2026-11-11.json")); res = [r for r in d["results"] if r["error"] is None]
    print(f"calls {len(d['results'])} errors {len(d['results'])-len(res)}")
    print(f"{'model':<28}{'fmt':<7}{'n':>4}{'parsed':>8}{'correct':>9}{'CI(correct)':>16}{'in':>7}{'out':>6}{'$/1000':>9}{'p50 s':>7}{'max stop':>10}")
    for m in d["models"]:
        for f in ("plain", "json", "xml"):
            rr = [r for r in res if r["model"] == m and r["fmt"] == f]
            if not rr: continue
            n = len(rr); k = sum(r["ok"] for r in rr); lo, hi = wilson(k, n)
            c = statistics.mean(estimate_usd("anthropic:" + m, r["in"], r["out"]) for r in rr) * 1000
            mx = sum(r["stop"] == "max_tokens" for r in rr)
            print(f"{m:<28}{f:<7}{n:>4}{sum(r['parsed'] for r in rr):>8}{k:>9}{lo:>9.2f}-{hi:.2f}{statistics.mean(r['in'] for r in rr):>7.0f}{statistics.mean(r['out'] for r in rr):>6.1f}{c:>9.4f}{statistics.median(r['secs'] for r in rr):>7.2f}{mx:>10}")
    print("\nfailures (not parsed) by model and format, first reply shown:")
    for m in d["models"]:
        for f in ("json", "xml"):
            bad = [r for r in res if r["model"] == m and r["fmt"] == f and not r["parsed"]]
            if bad: print(f"  {m} {f}: {len(bad)} unparsed; e.g. {bad[0]['text'][:90]!r}")
    fo = d["failover"]
    print(f"\nfailover probe n={len(fo)}: failed-call wall time median {statistics.median(x['fail_secs'] for x in fo):.3f}s max {max(x['fail_secs'] for x in fo):.3f}s; fallback call median {statistics.median(x['fallback_secs'] for x in fo):.3f}s; error text: {fo[0]['err']}")
if __name__ == "__main__": main()
