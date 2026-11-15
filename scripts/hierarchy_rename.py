#!/usr/bin/env python3
"""Chapter 6 failure injection: a team is renamed and a product moves, both in the middle of October.

SYNTHETIC. Daily cost for the nl-query product is $21,000 over October, spread evenly for clarity.
We compare two ways to roll the month up by team: as-of the date of spend (effective-dated), and
by today's owner (history rewritten).
"""
from datetime import date, timedelta
from costlab.hierarchy import Assignment, owner_on, latest_owner, check_gaps_and_overlaps, TeamName, name_on

T = [
    Assignment("nl-query", "Insights Platform", date(2026, 1, 1), date(2026, 10, 16)),
    Assignment("nl-query", "Data Products",     date(2026, 10, 16), None),   # reorganisation, 16 October
]
days = [date(2026, 10, 1) + timedelta(d) for d in range(31)]
daily = 21_000 / 31
asof, rewritten = {}, {}
for d in days:
    asof[owner_on(T, "nl-query", d)] = asof.get(owner_on(T, "nl-query", d), 0) + daily
    rewritten[latest_owner(T, "nl-query")] = rewritten.get(latest_owner(T, "nl-query"), 0) + daily
print("as-of the date of spend:")
for k, v in sorted(asof.items()): print(f"  {k:20s} ${v:>9,.0f}")
print("by today's owner (history rewritten):")
for k, v in sorted(rewritten.items()): print(f"  {k:20s} ${v:>9,.0f}")
print("integrity:", check_gaps_and_overlaps(T, "nl-query", days[0], days[-1]) or "no gaps, no overlaps")
bad = T + [Assignment("nl-query", "Insights Platform", date(2026, 10, 10), date(2026, 10, 20))]
print("after a sloppy edit:", check_gaps_and_overlaps(bad, "nl-query", days[0], days[-1])[:2], "...")

# shared cache: split by metered share of calls, not by who owns the cost object today
shared = 3_000.0
calls = {"support-agent": 61_000, "knowledge-assistant": 27_000, "nl-query": 12_000}
tot = sum(calls.values())
print("\nshared prompt-cache service, $3,000, split by metered share of calls:")
for k, v in calls.items(): print(f"  {k:22s} {v/tot:6.1%}  ${shared*v/tot:>8,.0f}")

# a rename with no change of owner: team id T7 is "Support Automation" until 16 October, "Customer Resolution" after
names = [TeamName("T7", "Support Automation", date(2026, 1, 1), date(2026, 10, 16)),
         TeamName("T7", "Customer Resolution", date(2026, 10, 16))]
sa_daily = 25_350 / 31
by_label, by_id = {}, {}
for d in days:
    by_label[name_on(names, "T7", d)] = by_label.get(name_on(names, "T7", d), 0) + sa_daily
    by_id["T7"] = by_id.get("T7", 0) + sa_daily
print("\nsupport-agent, $25,350, team T7 renamed on 16 October (same owner):")
print("  grouped by label in the cost data:")
for k, v in sorted(by_label.items()): print(f"    {k:22s} ${v:>9,.0f}")
print("  grouped by team id, label looked up for the report date:")
for k, v in by_id.items(): print(f"    {k} ({name_on(names, 'T7', days[-1])})  ${v:>9,.0f}")

# the shared cache joined by two more products on 20 October: the method changes from that date, history stays
print("\nshared cache, $3,000 for October. Method A (support-agent only) before 20 October; method B (metered share) from 20 October:")
daily_cache = 3_000 / 31
pre = [d for d in days if d < date(2026, 10, 20)]
post = [d for d in days if d >= date(2026, 10, 20)]
alloc = {"support-agent": len(pre) * daily_cache, "knowledge-assistant": 0.0, "nl-query": 0.0}
post_calls = {"support-agent": 40_000, "knowledge-assistant": 35_000, "nl-query": 25_000}
tp = sum(post_calls.values())
for k, v in post_calls.items():
    alloc[k] += len(post) * daily_cache * v / tp
for k, v in alloc.items(): print(f"  {k:22s} ${v:>8,.0f}")
print(f"  total ${sum(alloc.values()):,.0f}  ({len(pre)} days under A, {len(post)} under B; calls from 20 October are assumed)")
