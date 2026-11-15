#!/usr/bin/env python3
"""Chapter 30: commitment scenarios. Arithmetic over SYNTHETIC Fieldstone usage; the 5.99x per-task price move comes from the recorded shadow run (see tokenizer_summary.py).
ASSUMED: 15 percent committed-spend discount, 12-month term, usage starts $60,000 a month at list. No vendor offers these terms as published rates."""
import statistics
from costlab.commitments import *
RATIO_LIST = 0.10          # list price per token on the newer model against the older
RATIO_TASK = 1 / 5.99      # measured cost per task ratio, ancestor to successor (tokenizer_summary.py)
def row(name, r): print(f"{name:<54} paid ${r['paid']:>10,.0f}  used ${r['used']:>10,.0f}  shortfall ${r.get('shortfall',0):>9,.0f}")
def main():
    print("== A. Size of the commit against three growth paths (12 months, discount 15 percent, usage at list starts 60,000/month) ==")
    for g in (0.00, 0.05, 0.10):
        u = usage_path(12, 60000, g, seed=3)
        for share in (0.6, 0.8, 1.0, 1.2):
            commit = share * 12 * 60000 * 0.85
            r = spend_commit(u, 0.15, commit)
            print(f"growth {g:.2f} commit {share:.1f}x flat-year  list ${r['list']:>10,.0f}  paid ${r['paid']:>10,.0f}  vs list {r['effective_vs_list']*100:5.1f}%  shortfall ${r['shortfall']:>9,.0f}")
    print("\n== B. The price you did not get: from month 5 the work moves to the newer model; the commit is in old-price dollars ==")
    u = usage_path(12, 60000, 0.05, seed=3); commit = 12 * 60000 * 0.85
    for label, ratio in (("no move", 1.0), ("per-task ratio measured 0.167", RATIO_TASK), ("list ratio 0.10", RATIO_LIST)):
        v = price_cut_path(u, 5, ratio); r = spend_commit(v, 0.15, commit)
        un = sum(v) * 0.85
        print(f"{label:<34} usage at new list ${sum(v):>10,.0f}  discounted ${un:>10,.0f}  commit ${commit:,.0f}  paid ${r['paid']:>10,.0f}  shortfall ${r['shortfall']:>9,.0f}  paid per $ of work at old-list-equivalent {r['paid']/sum(u):.3f}")
    v = price_cut_path(u, 5, RATIO_TASK); r = spend_commit(v, 0.15, commit)
    print(f"   same work, nothing wasted by the product team; the invoice still reads the commit: paid ${r['paid']:,.0f} against ${sum(v):,.0f} at plain list on the newer model = {r['paid']/sum(v)*100:.0f}% of list")
    print("\n== C. Monthly use-it-or-lose-it floor against full-period commit, same shock ==")
    v = price_cut_path(u, 5, RATIO_TASK)
    row("full period commit", spend_commit(v, 0.15, commit)); row("monthly floor 85 percent of month-1", monthly_floor_commit(v, 0.15, 0.85 * u[0] * 0.85))
    print("\n== D. Provisioned capacity: break-even and traffic shape (SYNTHETIC demand, ASSUMED prices) ==")
    for prem in (1.67, 1.27, 0.70, 0.50):
        print(f"capacity price {prem:.2f}x on-demand per token at full use -> break-even utilisation {breakeven_utilisation(prem, 1.0)*100:.0f}%")
    d = diurnal_demand(seed=4); peak = max(d); mean = statistics.mean(d)
    print(f"demand: peak {peak:,.0f}, mean {mean:,.0f} units/minute; mean over peak {mean/peak*100:.1f}%")
    for prem in (1.0, 0.70, 0.50):
        best = None
        for cap in range(0, int(peak) + 1, 25):
            r = provisioned_cost(d, cap, prem * 1.0 / 60, 1.0 / 60)   # units per minute; price per unit-minute scaled so on-demand = 1/60 per unit-minute-hour
            if best is None or r["total"] < best[1]["total"]: best = (cap, r)
        allod = sum(x for x in d) * 1.0 / 60
        print(f"capacity at {prem:.2f}x on-demand rate: best capacity {best[0]:>5} ({best[0]/peak*100:4.1f}% of peak)  total {best[1]['total']/allod*100:5.1f}% of all-on-demand  utilisation {best[1]['utilisation']*100:5.1f}%")
    print("   capacity sized to peak at 0.70x rate:", end=" ")
    r = provisioned_cost(d, peak, 0.70 / 60, 1.0 / 60); print(f"{r['total']/(sum(d)/60)*100:.1f}% of all-on-demand, utilisation {r['utilisation']*100:.1f}%")
if __name__ == "__main__": main()
