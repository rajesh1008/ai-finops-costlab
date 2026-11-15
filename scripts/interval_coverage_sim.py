#!/usr/bin/env python3
"""Chapter 45 follow-up (nineteenth run), OFFLINE SIMULATION, no API calls. Question: a team measures n runs of an agent task, builds a 90 percent interval for the NEXT run's cost, and the cost per run
is lognormal with a geometric standard deviation (GSD) of 1.34 (the median figure for repeats of one task reported in arXiv 2608.25399, seen as an excerpt; used here only as an ASSUMED spread).
Three interval rules built from the n observed costs: (a) naive normal on the raw costs, mean +- 1.645 s; (b) the same on logs, back-transformed; (c) a prediction interval on logs with the t quantile and sqrt(1+1/n).
60,000 simulated futures per cell, seed 11. Reports empirical coverage of the next run and mean width as a ratio of the true median. Also reports the 95th-percentile-to-median ratio at GSD 1.34 and 2.0."""
import math, random, statistics as st
from pathlib import Path
T90 = {3: 2.920, 5: 2.132, 10: 1.833, 20: 1.729, 30: 1.699}   # t quantile 0.95 with n-1 degrees of freedom
def run(n, gsd, trials=200_000, seed=11):
    rng = random.Random(seed); sig = math.log(gsd); cov = {"a": 0, "b": 0, "c": 0}; wid = {"a": 0.0, "b": 0.0, "c": 0.0}
    for _ in range(trials):
        x = [math.exp(rng.gauss(0, sig)) for _ in range(n)]; nxt = math.exp(rng.gauss(0, sig))
        m, s = st.mean(x), st.stdev(x); lo, hi = m - 1.645 * s, m + 1.645 * s
        cov["a"] += lo <= nxt <= hi; wid["a"] += hi - lo
        l = [math.log(v) for v in x]; lm, ls = st.mean(l), st.stdev(l)
        lo, hi = math.exp(lm - 1.645 * ls), math.exp(lm + 1.645 * ls); cov["b"] += lo <= nxt <= hi; wid["b"] += hi - lo
        k = T90[n] * math.sqrt(1 + 1 / n); lo, hi = math.exp(lm - k * ls), math.exp(lm + k * ls); cov["c"] += lo <= nxt <= hi; wid["c"] += hi - lo
    return {r: (cov[r] / trials, wid[r] / trials) for r in cov}
lines = ["GSD assumed 1.34: 95th percentile / median = %.3f; at GSD 2.0: %.3f" % (math.exp(1.645 * math.log(1.34)), math.exp(1.645 * math.log(2.0))),
         "n | rule a (raw normal) coverage, width/median | rule b (log normal) | rule c (log t, prediction)"]
for gsd in (1.34,):
    for n in (3, 5, 10, 20, 30):
        r = run(n, gsd, trials=60_000)
        lines.append(f"n={n} GSD={gsd}: " + " | ".join(f"{k} {v[0]*100:.1f}% w={v[1]:.2f}" for k, v in r.items()))
r = run(5, 2.0, trials=60_000); lines.append("n=5 GSD=2.0: " + " | ".join(f"{k} {v[0]*100:.1f}% w={v[1]:.2f}" for k, v in r.items()))
Path(__file__).resolve().parents[1].joinpath("runs", "interval-coverage-sim-2026-11-11.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
