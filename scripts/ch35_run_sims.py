#!/usr/bin/env python3
"""Offline arithmetic and simulations for the thirty-fifth run sections (Ch7, 15, 31, 38, 43, 44). Every input is invented and labelled so in the text. No API calls."""
import random, math
def ch07(seed=7):
    r = random.Random(seed)
    # 400 users, each opens a conversation, then returns after a gap drawn from a mixture: quick follow-ups, same-day returns, next-day returns
    events = []
    for u in range(400):
        t = r.uniform(0, 600)  # minutes after 08:00
        for _ in range(r.randint(2, 6)):
            events.append((u, t))
            g = r.choices([r.uniform(0.5, 8), r.uniform(15, 90), r.uniform(240, 1000)], [0.65, 0.25, 0.10])[0]
            t += g
    out = {}
    for th in (10, 30, 60, 120):
        sessions = 0; last = {}
        for u, t in sorted(events, key=lambda e: (e[0], e[1])):
            if u not in last or t - last[u] > th: sessions += 1
            last[u] = t
        out[th] = sessions
    return len(events), out
def ch15():
    rows = []
    for r_ in (2000, 4000, 7843, 8000, 12000):
        hybrid = 4000 + 0.99 * r_; pure = 1.5 * r_
        rows.append((r_, round(hybrid), round(pure), round(hybrid / r_, 2)))
    return rows
def ch31():
    calls = 1200 * 120; prefix = 5000; fresh = 330
    full_read = calls * (fresh + prefix * 0.1) * 1e-6
    windows = 120 // 5; prefixes = 6
    cold_extra = windows * prefixes * prefix * (1.25 - 0.1) * 1e-6
    return calls, round(full_read, 2), windows * prefixes, round(cold_extra, 2)
def ch38():
    rows = []
    for spend in (0.5e6, 1e6, 3e6, 6e6, 12e6):
        buy = max(2000, 0.01 * spend); build = 30000
        rows.append((int(spend), round(buy), build))
    return rows, 30000 / 0.01
def ch43():
    a, b = 412000, 380000
    return round(a / 31), round(b / 28), round((b / 28) / (a / 31) - 1, 4), round(b / a - 1, 4)
def ch44():
    out = []
    for p in (0.015, 0.005, 0.001):
        runs = 4000; pages = runs * p
        out.append((p, pages, pages * 10 / 60))
    return out
if __name__ == "__main__":
    print("ch07", ch07()); print("ch15", ch15()); print("ch31", ch31()); print("ch38", ch38()); print("ch43", ch43()); print("ch44", ch44())

def ch30():
    usage = [30, 34, 38, 41, 44, 46, 48, 50, 51, 52, 52, 53]  # $ thousands a month, invented ramp
    commit = 45  # $ thousand a month, committed
    paid = sum(max(u, commit) for u in usage); used = sum(usage)
    short = sum(max(0, commit - u) for u in usage)
    annual = commit * 12
    # annual pool: pay max(annual commit, used)
    pool = max(annual, used)
    # discount 15 percent on committed usage
    disc = 0.15
    list_cost = used
    take_or_pay_cost = sum(max(u * (1 - disc), commit * (1 - disc)) for u in usage)
    pool_cost = max(annual * (1 - disc), used * (1 - disc))
    return dict(used=used, annual=annual, short_monthly=short, paid_monthly=paid, list=list_cost, monthly_tp=round(take_or_pay_cost, 2), pool=round(pool_cost, 2))
