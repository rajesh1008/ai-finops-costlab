#!/usr/bin/env python3
"""Chapter 9: three views from one SYNTHETIC call-grain dataset, plus the invoice-drift injection. No API."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from costlab.views import *

rows = generate()
print(f"SYNTHETIC dataset: {len(rows)} call rows, {len({r.session for r in rows})} sessions, 30 days, seed 21")
fin = finance_view(rows)
print(f"\nFinance view: total ${fin['total']:.2f}; attribution coverage {fin['coverage']:.1%}")
for t, v in sorted(fin["by_team"].items(), key=lambda kv: -kv[1]):
    print(f"  {t:10s} ${v:8.2f}  {v/fin['total']:.1%}")
print("\nBoard view (cost per accepted outcome; coverage on the same page: %.1f%%)" % (fin["coverage"]*100))
for p, (s, o, c) in board_view(rows).items():
    print(f"  {p:20s} spend ${s:8.2f} outcomes {o:5d} cost per outcome ${c:.4f}")
print("\nEngineer view: top three sessions by cost")
top = top_sessions(rows)
for s, c in top:
    n = sum(1 for r in rows if r.session == s)
    print(f"  {s:8s} ${c:.4f} steps {n}")
sid = top[0][0]
print(f"Decomposition of {sid} (first 3 and last step; columns: input, output, cache read, cache write, total USD)")
ev = engineer_view(rows, sid)
for e in ev[:3] + ev[-1:]:
    print("  step %2d  %.4f %.4f %.4f %.4f  %.4f" % e)
cr = sum(e[3] for e in ev) / sum(e[5] for e in ev)
print(f"  cache read is {cr:.1%} of this session's cost")

d = daily(rows)
inv = invoice_view_daily(rows, 30)
med = sorted(d.values())[15]
print(f"\nInjection: invoice-built daily view versus meter-built daily view (spike injected on day 19)")
print(f"  meter day 19 ${d[19]:.2f}; median day ${med:.2f}; ratio {d[19]/med:.2f}")
print(f"  invoice view shows ${inv[19]:.2f} every day; day-19 error {abs(d[19]-inv[19])/d[19]:.1%}")
print(f"  largest single-day gap between views: day {max(d, key=lambda k: abs(d[k]-inv[k]))} ${max(abs(d[k]-inv[k]) for k in d):.2f}")
no = [r for r in rows if r.session != top[0][0]]
print(f"  without the runaway session the meter would read ${sum(r.cost for r in no):.2f}; with it ${sum(r.cost for r in rows):.2f}")
print(f"  runaway session share of the month: {top[0][1]/sum(r.cost for r in rows):.1%}")
