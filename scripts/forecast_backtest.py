#!/usr/bin/env python3
"""Chapter 13: backtest a trend line and a driver model on an 18-month SYNTHETIC history; interval from three driver ranges. No API."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.forecast import *

h = history()
print("SYNTHETIC history, seed 13. Events built in: agent launch in month 9 (tasks x1.6, cost per task x1.25); vendor price cut of 35% from month 13.")
print("month  users   tasks/user  $/task   spend")
for r in h[::3] + [h[-1]]:
    print(f"{r['m']:5d} {r['users']:7.0f} {r['tpu']:9.1f} {r['cpt']:8.3f} {r['spend']:10,.0f}")
act = lambda a, b: [x["spend"] for x in h if a <= x["m"] <= b]
print("\nBacktest, three-month horizon, forecast made at the end of month `at`:")
print("at   horizon  trend MAPE  driver(naive) MAPE  driver(told about the event) MAPE")
for at in (6, 8, 11, 14):
    hz = 3
    a = act(at + 1, at + hz)
    t = trend_forecast(h, at, hz)
    d = driver_forecast(h, at, hz, 0.07, 0.03)
    cp = {13: -0.35} if at < 13 <= at + hz else {}
    ev = driver_forecast(h, at, hz, 0.07, 0.03, cp)
    print(f"{at:3d}  {at+1}-{at+hz}   {mape(t, a):9.1%}   {mape(d, a):14.1%}            {mape(ev, a):10.1%}")
print("\nMonth 9 launch is not an input to any of these forecasts unless the model is told: the driver model with cost per task and tasks per user held at last values is wrong at month 8 for that reason.")
last = [r for r in h if r["m"] == 18][0]
s = monte_carlo(last, 6)
print(f"\nSix months after month 18 (SYNTHETIC ranges: users +4 to +10% a month, tasks per user 0 to +6%, cost per task -3 to +2%):")
print(f"  month 18 spend ${last['spend']:,.0f}; month 24 spend p10 ${s[len(s)//10]:,.0f}  median ${s[len(s)//2]:,.0f}  p90 ${s[9*len(s)//10]:,.0f}")
print(f"  p90 / p10 = {s[9*len(s)//10]/s[len(s)//10]:.2f}")
