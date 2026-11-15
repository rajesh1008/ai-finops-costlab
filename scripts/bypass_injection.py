#!/usr/bin/env python3
"""Chapter 42 failure injection (nineteenth run), OFFLINE SIMULATION, no API calls, all numbers ASSUMED. 60 days of daily invoice and daily gateway ledger for a firm whose spend is about $6,500 a day
(an assumed figure; the book's month-two bill is $196,000). On day 21 a notebook key that bypasses the gateway starts spending a share `s` of the daily total. The gateway ledger never sees it, so tagged coverage
(measured on ledger rows) is unchanged; the daily residual (invoice minus ledger) is the only thing that moves. Daily noise: ledger/invoice timing mismatch of +-1.2 percent of the day's spend (uniform, seed 3).
Detector: residual share above a threshold for k consecutive days. Reports the day each (s, threshold, k) combination detects, the false alarms before day 21, and the dollars spent unseen before detection."""
import random
from pathlib import Path
def simulate(s, thr, k, seed=3, days=60, start=21, daily=6500.0, noise=0.012):
    rng = random.Random(seed); run = 0; det = None; false = 0; unseen = 0.0
    for d in range(1, days + 1):
        spend = daily * rng.uniform(0.9, 1.1); byp = spend * s if d >= start else 0.0
        resid = (byp + spend * rng.uniform(-noise, noise)) / spend
        run = run + 1 if resid > thr else 0
        if d >= start and det is None: unseen += byp
        if run >= k and det is None:
            det = d
            if d < start: false += 1
        if run >= k and d < start: false = max(false, 1)
    return det, false, unseen
lines = ["bypass share s | threshold | consecutive days k | detected on day | false alarm before day 21 | bypassed dollars before detection (ASSUMED $6,500/day)"]
for s in (0.02, 0.04, 0.06, 0.10):
    for thr in (0.01, 0.02):
        for k in (1, 3):
            det, fa, unseen = simulate(s, thr, k)
            lines.append(f"{s:.2f} | {thr:.2f} | {k} | {det if det else 'never'} | {'yes' if fa else 'no'} | ${unseen:,.0f}")
out = Path(__file__).resolve().parents[1] / "runs" / "bypass-injection-2026-11-11.txt"; out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))
