#!/usr/bin/env python3
"""Chapter 44 summary of runs/killswitch-lab-2026-11-11.json plus the composed night-incident arithmetic."""
import json, statistics as st
from pathlib import Path
from costlab.killswitch import time_to_stop, incident_cost
import sys
F = "killswitch-partial-lab-2026-11-11.json" if len(sys.argv) > 1 and sys.argv[1] == "partial" else "killswitch-nudge-lab-2026-11-11.json" if len(sys.argv) > 1 and sys.argv[1] == "nudge" else "killswitch-lab-2026-11-11.json"
d = json.loads((Path(__file__).resolve().parents[1] / "runs" / F).read_text())["results"]
print(F)
for m in ("h45", "h55"):
    for c in ("none", "breaker", "cap"):
        rs = [r for r in d if r["m"] == m and r["control"] == c]
        reasons = {}
        for r in rs: reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
        print(f"{m} {c}: n={len(rs)} median steps={st.median(r['steps'] for r in rs)} max steps={max(r['steps'] for r in rs)} mean cost=${st.mean(r['cost'] for r in rs):.4f} max cost=${max(r['cost'] for r in rs):.4f} reasons={reasons}")
# COMPOSED night: loop rate per minute, stop times
rate = 31.0   # ASSUMED dollars per minute at full ramp across the fleet
hum = time_to_stop(detect_min=15, page_min=25, decide_min=40, act_min=10)
auto = time_to_stop(detect_min=0.5, page_min=0, decide_min=0, act_min=0.5)
print("human-only minutes to stop:", hum, "cost with 10-minute ramp: $%.0f" % incident_cost(rate, hum, 10))
print("breaker at gateway minutes to stop:", auto, "cost: $%.0f" % incident_cost(rate, auto, 10))
