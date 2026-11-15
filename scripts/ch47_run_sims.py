#!/usr/bin/env python3
"""47th run: arithmetic behind the new sections in Ch21, 29, 30, 32, 34, 37-42, 44-46, 48. All inputs are INVENTED illustrations, stated as such in the chapters."""
def ch21():
    saving = 0.0035; calls = 2_000_000
    out = []
    for n in (5_000, 20_000, 50_000):
        label = n * 0.012; review = n * 0.05 * 0.40; train = {5_000: 150, 20_000: 400, 50_000: 900}[n]
        total = label + review + train
        monthly = saving * calls
        out.append((n, round(label), round(review), train, round(total), round(total / monthly * 30, 1)))
    return out
def ch29():
    a = b = 0.004; tie = 0.02; d = 0.12; strong = 0.02
    per = a + b + d * tie
    return round(per, 4), strong, round(1 - per / strong, 3), round(per * 100_000), round(strong * 100_000)
def ch30():
    commit = 600_000; usage = 520_000; short = commit - usage
    eff = commit / usage
    roll = min(short, 0.2 * commit)  # rollover credit if allowed up to 20% of commit
    # with 10% rollover cap
    roll10 = min(short, 0.1 * commit)
    return short, round(eff, 4), round(short / commit, 3), roll10, round((commit - roll10) / usage, 4)
def ch32():
    req = 400_000; falsep = 0.004; ticket = 9.0; retry_cost = 0.002
    blocked = req * falsep
    tickets = blocked * 0.02
    return round(blocked), round(blocked * retry_cost, 2), round(tickets), round(tickets * ticket), 
def ch34():
    before = dict(collect=14, tie=6, write=8, review=4); after = dict(collect=3, tie=6, write=8, review=4)
    rate = 95
    sb, sa = sum(before.values()), sum(after.values())
    return sb, sa, sb * rate, sa * rate, (sb - sa) * rate * 4
def ch37():
    spend = 1_200_000; fte = 0.2 * 180_000
    return fte, [round(spend * r) for r in (0.03, 0.05, 0.08)], [round(spend * r - fte) for r in (0.03, 0.05, 0.08)]
def ch38():
    seats = 40; per = 90 * 12
    seatcost = seats * per
    usage_rate = 0.0004; records = 90_000_000
    usage = usage_rate * records
    cross = seatcost / usage_rate
    return seatcost, usage, round(cross)
def ch40():
    spend_usd = 420_000; rev_eur = 2_000_000; fx0 = 1.08; fx1 = 1.03
    # costs in USD, revenue in EUR; margin in USD terms
    r0 = rev_eur * fx0; r1 = rev_eur * fx1
    return r0, r1, r0 - r1, round(spend_usd / r0, 4), round(spend_usd / r1, 4)
def ch41():
    rows = {}
    for months, hours in ((3, 30), (6, 30), (12, 30), (3, 10)):
        n = 12 / months; assess = n * hours * 95; slip = months / 2 * 2500
        rows[(months, hours)] = (round(assess), round(slip), round(assess + slip))
    return rows
def ch42():
    weeks = [10, 14, 16, 16, 14, 12, 12, 10, 10, 8, 8, 6]
    return sum(weeks), sum(weeks) * 95, sum(weeks[:6]), sum(weeks) + 60 + 20, sum(weeks) * 95 + 5700 + 1900
def ch42b():
    return [round((1.96 * cv / 0.05) ** 2, 1) for cv in (0.10, 0.25, 0.06)]
def ch44():
    saving = (3.0 - 1.5) * 4000; cost = 5 * 40 * 95
    return saving, cost, round(cost / saving, 2), round((cost + 1200) / saving, 2)
def ch45():
    extra = 0.6 * 100_000 * 5 / 4.345
    import math
    t = 10500 / 12000; p = (0.038 / 10500) / (0.05 / 12000)
    return round(extra), round(extra / (300_000 + extra), 3), round(math.log(t) / math.log(0.76), 3)
def ch46():
    return round(0.22 * 0.15, 3), round(0.48 * 0.15, 3)
def ch48():
    return round(283 * 5 / 1e6, 6), round(1016 * 0.5 / 1e6, 6), round(283 * 5 / (1016 * 0.5), 2)
def ch33():
    from math import log, exp
    from statistics import NormalDist as N
    mu, s = log(8), 1.0
    def E(c): return exp(mu + .5) * N().cdf((mu + 1 - log(c)) / s) - c * N().cdf((mu - log(c)) / s)
    mean = exp(mu + .5)
    return round(mean, 2), round(1 - N().cdf((log(15) - mu) / s), 3), round(1 - N().cdf((log(15) - mu - 1) / s), 3), round(E(41.45), 2), round(E(30), 2), round(E(22.5), 2)
def ch35():
    return [round(2 * (1.96 + 0.8416) ** 2 * cv ** 2 / 0.05 ** 2) for cv in (1.2, 2.0)]
def ch36():
    d = {"A": 50000, "B": 30000, "C": 20000}; c = {"A": 10, "B": 40, "C": 50}
    return {k: (d[k] + 30000 * d[k] / 100000, d[k] + 10000, d[k] + 30000 * c[k] / 100) for k in d}
def ch47():
    return 1.8e6 * (3000 * 1 + 400 * 5) / 1e6, 1.8e6 * (1500 + 2000) / 1e6, 1.8e6 * (6000 + 2000) / 1e6, 900_000 * (1500 + 2000) / 1e6, 3_600_000 * 8000 / 1e6
if __name__ == "__main__":
    for f in (ch21, ch29, ch30, ch32, ch33, ch34, ch35, ch36, ch37, ch38, ch40, ch41, ch42, ch42b, ch44, ch45, ch46, ch47, ch48):
        print(f.__name__, f())
