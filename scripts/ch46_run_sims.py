#!/usr/bin/env python3
"""Arithmetic for the forty-sixth run's invented examples (Ch1, 3, 10, 11, 14, 17, 18, 19, 22, 27, 31, 36). Offline, seeded, no API calls."""
import math, random, statistics as st

def ch1():
    base = 180_000.0
    vol, mix, price = 1.30, 1.15, 0.90
    steps = [base, base * vol, base * vol * mix, base * vol * mix * price]
    return dict(steps=steps, factor=vol * mix * price, contributions=[steps[1] - steps[0], steps[2] - steps[1], steps[3] - steps[2]])

def ch3():
    weekday, weekend = 5_000.0, 2_000.0           # invented daily spend
    month = 22 * weekday + 8 * weekend            # 30 days, 22 weekdays
    est_from_weekdays = 30 * weekday
    est_from_weekend = 30 * weekend
    est_from_mon_sun = 30 * (5 * weekday + 2 * weekend) / 7
    return dict(month=month, wk=est_from_weekdays, we=est_from_weekend, week=est_from_mon_sun)

def ch10(seed=10):
    rnd = random.Random(seed)
    days = []
    for d in range(28 * 12):
        f = 0.45 if d % 7 in (5, 6) else 1.0
        days.append(rnd.lognormvariate(math.log(4000 * f), 0.12))
    mu, sd = st.mean(days), st.pstdev(days)
    naive = sum(1 for x in days if x > mu + 3 * sd or x < mu - 3 * sd)
    naive_hi = sum(1 for x in days if x > mu + 2 * sd)
    # per weekday baseline
    fa = 0
    for w in range(7):
        g = [x for d, x in enumerate(days) if d % 7 == w]; m, s = st.mean(g), st.pstdev(g)
        fa += sum(1 for x in g if x > m + 3 * s)
    # a real 1.6x spike on a Wednesday (d%7==2) and on a Sunday (d%7==6) against the naive threshold
    wed, sun = 4000 * 1.6, 4000 * 0.45 * 1.6
    thr = {}
    for w in (2, 6):
        g = [x for d, x in enumerate(days) if d % 7 == w]; thr[w] = st.mean(g) + 3 * st.pstdev(g)
    return dict(mu=mu, sd=sd, thr=mu + 3 * sd, naive=naive, naive_hi=naive_hi, per_weekday=fa, wed=wed, sun=sun, n=len(days), thr_wed=thr[2], thr_sun=thr[6])

def ch11():
    call, accept, review = 0.04, 0.80, 1.20
    cost_per_accepted_no_review = call / accept
    # rejected outputs go to a person at $review each; accepted count includes human-fixed ones
    total_per_task = call + (1 - accept) * review
    return dict(a=cost_per_accepted_no_review, b=total_per_task, accept_needed=1 - (0.09 - call) / review)

def ch14():
    # Fieldstone vs peer median, cost per 1,000 requests, by task type (invented)
    ours = {"simple": (0.50, 0.70), "hard": (9.00, 0.30)}     # (cost per 1000, share of our traffic)
    peer = {"simple": (0.40, 0.30), "hard": (8.00, 0.70)}
    ours_blend = sum(c * w for c, w in ours.values())
    peer_blend = sum(c * w for c, w in peer.values())
    std = sum(ours[k][0] * peer[k][1] for k in ours)         # our prices on the peer mix
    return dict(ours=ours_blend, peer=peer_blend, ours_on_peer_mix=std)

def ch17():
    cheap, strong = 0.002, 0.020; easy = 0.7
    def cost(err_hard_to_cheap, err_easy_to_strong, escalate=0.0):
        hard = 1 - easy
        c = easy * ((1 - err_easy_to_strong) * cheap + err_easy_to_strong * strong)
        c += hard * ((1 - err_hard_to_cheap) * strong + err_hard_to_cheap * cheap)
        return c
    perfect = cost(0, 0); noisy = cost(0.15, 0.10)
    allstrong = strong
    # quality: share of hard queries answered by cheap model times assumed failure
    hard_share = 1 - easy
    miss_hard = 0.15 * hard_share
    return dict(perfect=perfect, noisy=noisy, allstrong=allstrong, hard_missed=miss_hard, saving_noisy=1 - noisy / allstrong,
                breakeven_cost_of_wrong=(allstrong - noisy) / miss_hard)

def ch18():
    wr, rd = 1.25, 0.10   # multiples of input price
    need = (wr - 1.0) / (1.0 - rd)       # reads per write to break even against no cache
    p = need / (1 + need)
    lam = -math.log(1 - p) / 5           # per minute, 5-minute TTL refreshed on hit
    return dict(need=need, p=p, per_min=lam, per_hour=lam * 60)

def ch19():
    sys_tokens, calls_month, price = 4000, 2_000_000, 3.0
    full = sys_tokens * calls_month * price / 1e6 * 12
    trimmed = 2400 * calls_month * price / 1e6 * 12
    return dict(full=full, trimmed=trimmed, saved=full - trimmed, eng_days=(full - trimmed) / 1500)

def ch22():
    # hedged request: send a second copy when first has not answered by p95 latency
    n = 1_000_000; c = 0.01
    extra = 0.05 * n * c          # 5 percent hedged, assume both billed in full
    cancelled = 0.05 * n * c * 0.4   # if cancellation recovers 60 percent of the duplicate
    return dict(extra=extra, extra_with_cancel=cancelled, base=n * c)

def ch27():
    rungs = [("full model", 0.050, 0.96), ("small model", 0.008, 0.90), ("cached answer or template", 0.0005, 0.70)]
    out = []
    for name, c, q in rungs: out.append((name, c, q, c / q))
    # a day with 100,000 requests, 15 percent pushed to rung two, 5 percent to rung three, rest rung one
    mix = [0.80, 0.15, 0.05]
    cost = sum(m * r[1] for m, r in zip(mix, rungs)) * 100_000
    allfull = 0.050 * 100_000
    quality = sum(m * r[2] for m, r in zip(mix, rungs))
    return dict(rows=out, cost=cost, allfull=allfull, quality=quality)

def ch31():
    # two vendors, switching cost
    a, b = 1.00, 0.85; spend = 400_000.0; switch = 60_000.0  # annual spend
    sv = spend * (1 - b / a); sv2 = spend * (1 - b / (a * 0.92))
    return dict(saving=sv, months=switch / sv * 12, saving_if_vendor_cuts=sv2, months_after_cut=switch / sv2 * 12)

def ch36():
    pool = 90_000.0; fixed = 0.30
    usage = {"Search": 520, "Support": 260, "Sales ops": 120, "Platform": 100}
    t = sum(usage.values())
    share = {k: pool * (fixed / len(usage) + (1 - fixed) * v / t) for k, v in usage.items()}
    return share

if __name__ == "__main__":
    for f in (ch1, ch3, ch10, ch11, ch14, ch17, ch18, ch19, ch22, ch27, ch31, ch36): print(f.__name__, f())
