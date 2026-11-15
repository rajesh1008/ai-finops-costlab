#!/usr/bin/env python3
"""Chapter 37 lab. Run three kinds of weekly review over 13 SYNTHETIC weeks with six planted events and record what each catches and when. No API calls."""
from costlab.review import *
def main():
    rows = build(); print("weekly total spend ($):", " ".join(f"{sum(r['spend'] for r in rows if r['week']==w)/1000:.0f}k" for w in range(1, 14)))
    print("planted events:"); [print(f"  week {w}: {e[0]} - {e[3]}") for w, e in EVENTS.items()]
    cause = {3: ("search", "volume"), 5: ("support-agent", "price"), 7: ("handbook", "cache"), 9: ("extraction", "tokens_per_call"), 10: ("support-agent", "mix"), 12: ("reports", "untagged")}
    res = {"total": {}, "product": {}, "driver": {}}; fa = {"total": 0, "product": 0, "driver": 0}; decisions = []
    for w in range(2, 14):
        t = review_total(rows, w); pr = review_product(rows, w); dr = review_driver(rows, w)
        for kind, hits in (("total", t), ("product", pr), ("driver", dr)):
            names = {h[0] for h in hits}
            if w in cause and (cause[w][0] in names or (kind == "total" and hits)): res[kind].setdefault(w, hits)
            elif hits and not (w in cause or w - 1 in cause): fa[kind] += 1
        if dr:
            for h in dr: decisions.append((w, h))
    print("\nWeeks 2 to 13 (12 reviews). Event caught in the week it happened? (total review = flags the company total only)")
    for w in cause:
        row = []
        for kind in ("total", "product", "driver"):
            row.append("caught" if w in res[kind] else "missed")
        print(f"  week {w:>2} {cause[w][0]:<14} {cause[w][1]:<16} total {row[0]:<7} by product {row[1]:<7} by driver {row[2]:<7}")
    print("\nCaught of 6:", {k: len(v) for k, v in res.items()}, " flags with no planted event (false alarms):", fa)
    print("\nDriver review: what it says (week, product, driver, $ change)")
    for w, h in decisions: print(f"  week {w:>2} {h[0]:<14} {h[1]:<16} {h[2]:>12,.0f}" if h[1] != 'untagged' else f"  week {w:>2} {h[0]:<14} untagged share {h[2]:.2f}")
    print(f"\nflags raised by driver review over the quarter: {len(decisions)}")
    # the sizes: what share of the company total did each event move
    print("\nSize of each event against the week's company total")
    for w, (p, k) in cause.items():
        a = next(r for r in rows if r['product']==p and r['week']==w-1); b = next(r for r in rows if r['product']==p and r['week']==w)
        tot_a = sum(r['spend'] for r in rows if r['week']==w-1)
        print(f"  week {w:>2} {p:<14} product spend {a['spend']:>9,.0f} -> {b['spend']:>9,.0f}  ({(b['spend']-a['spend'])/tot_a*100:+5.1f}% of last week's company total)")
if __name__ == "__main__": main()
