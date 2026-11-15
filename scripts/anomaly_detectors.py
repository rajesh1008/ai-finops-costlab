#!/usr/bin/env python3
"""Chapter 10: four ways to catch the Chapter 9 runaway, and what each costs in false alarms and in dollars. SYNTHETIC."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.views import generate, daily, top_sessions
from costlab.anomaly import trailing_median_alert, static_threshold_alert, session_cap_stop, scale_traffic

rows = generate()
d = daily(rows)
med = sorted(d.values())[15]
print(f"SYNTHETIC month (seed 21). Median day ${med:.2f}; runaway on day 19 (${d[19]:.2f}, {d[19]/med:.2f}x median)")
sid, scost = top_sessions(rows, 1)[0]
print(f"Runaway session {sid}: ${scost:.4f} over 90 steps")

print("\n1. Static daily ceiling")
for c in (3.0, 4.0, 5.0):
    hits = static_threshold_alert(d, c)
    print(f"   ceiling ${c:.2f}: alert days {hits if hits else 'none'}")
print("\n2. Trailing-median rule (7-day window)")
for pct in (0.25, 0.5, 0.64, 0.75):
    hits = trailing_median_alert(d, pct=pct)
    print(f"   exceed median by {pct:.0%}: alert days {hits if hits else 'none'}")
print("\n3. Gateway session cap (stops the session, runs while it is happening)")
for cap in (0.05, 0.10, 0.25, 0.50):
    step, spent = session_cap_stop(rows, sid, cap)
    print(f"   cap ${cap:.2f}: stopped at step {step}, spent ${spent:.4f}, avoided ${scost-spent:.4f} ({1-spent/scost:.1%} of the session)")
from collections import defaultdict
_t = defaultdict(float)
for r in rows: _t[r.session] += r.cost
ordinary = max(v for k, v in _t.items() if k != sid)
print(f"   largest ordinary session ${ordinary:.4f}; a cap at or above that never stops an ordinary session")

print("\n4. Planned launch on day 22 (traffic x2.0 from then on, SYNTHETIC) against rule 2 at 50 percent")
d2 = daily(scale_traffic(rows, 22, 2.0))
hits = trailing_median_alert(d2, pct=0.5)
print(f"   alert days {hits}; runaway day 19 included: {19 in hits}; days alerting for the launch: {[x for x in hits if x >= 22]}")
print(f"   launch alert run: {len([x for x in hits if x>=22])} of the 9 launch days alert (days {[x for x in hits if x>=22]})")

total = sum(d.values())
print(f"\nFinOps Foundation AI KPI, Anomaly Cost %: runaway extra spend over its day-19 baseline = ${d[19]-med:.2f} / ${total:.2f} = {(d[19]-med)/total:.1%}")
print(f"  whole session cost / month = {scost/total:.1%} (page's bands: green <2%, yellow 2-7%, red >7%)")
