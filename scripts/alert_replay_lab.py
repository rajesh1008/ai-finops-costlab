#!/usr/bin/env python3
"""Chapter 10 replay: 400 simulated months of 720 hours at 125 runs an hour (ASSUMED), per-run costs bootstrapped from the REAL Chapter 24 chain-lab runs.
Without an incident: false alerts per month for each rule. With an incident starting at hour 480 (day 21, midnight) in which an extra share of runs (2, 5, 10 percent) become tail-cost runs:
hours to first alert, and extra dollars spent before it. Rules: daily trailing median +50 percent (7 days), hourly spend above 1.5x the trailing 168-hour median, and 'hot run' count (at least k runs in an hour at or above the ordinary 99th percentile cost)."""
import json, numpy as np
from pathlib import Path
from costlab.agentrun import run_cost
from costlab.alertreplay import *
R = Path(__file__).resolve().parents[1] / "runs"
def main():
    d = json.load(open(R / "agent-run-lab-chain-2026-11-10.json")); res = [r for r in d["results"] if r["status"] != "api_error"]
    pool = sorted(run_cost(r["steps"], 1.0, 5.0) for r in res); tail = pool[-13:]; pm = np.mean(pool)
    print(f"pool n={len(pool)} mean ${pm:.5f} p99 ${np.quantile(pool, .99):.5f}; tail pool n=13 mean ${np.mean(tail):.5f}; ordinary month spend about ${pm*125*720:,.0f}")
    M = 400
    rules = {"daily median+50%": lambda s, h, st=0: (lambda x: None if x is None else x * 24)(first_day_alert_trailing_median(s.reshape(-1, 24).sum(1), start=st // 24)),
             "hourly 1.5x 168h median": lambda s, h, st=0: first_hour_alert_hourly(s, start=st), "hot runs >=8 an hour": lambda s, h, st=0: first_hour_alert_hot(h, 8, start=st), "hot runs >=15 an hour": lambda s, h, st=0: first_hour_alert_hot(h, 15, start=st)}
    print("\nNo incident: months with at least one alert, and alerts per month (first-alert only counted)")
    for name, f in rules.items():
        fired = 0
        for m in range(M):
            s, h = month(pool, tail, seed=m)
            if f(s, h) is not None: fired += 1
        print(f"  {name:<26} months with a false alert {fired}/{M} ({fired/M*100:.1f}%)")
    for extra in (0.02, 0.05, 0.10):
        print(f"\nIncident from hour 480: extra tail share {extra*100:.0f} percent of runs")
        for name, f in rules.items():
            delays, losts, miss = [], [], 0
            for m in range(M):
                s, h = month(pool, tail, inc_start=480, inc_extra=extra, seed=1000 + m); s0, h0 = month(pool, tail, seed=1000 + m)
                a = f(s, h, 480)
                if a is None: continue
                delays.append(a - 480); base = s0[480:a + 1].sum(); losts.append(s[480:a + 1].sum() - base)
            if delays: print(f"  {name:<26} detected {len(delays)}/{M}  median delay {np.median(delays):5.0f} h  p90 {np.percentile(delays, 90):5.0f} h  extra spend before alert median ${np.median(losts):7.2f}")
            else: print(f"  {name:<26} detected 0/{M}")
        s_full, _ = month(pool, tail, inc_start=480, inc_extra=extra, seed=5); s_base, _ = month(pool, tail, seed=5)
        print(f"  (the incident left unstopped to the end of the month costs about ${s_full[480:].sum()-s_base[480:].sum():,.0f} extra on a baseline of ${s_base.sum():,.0f})")
if __name__ == "__main__": main()
