#!/usr/bin/env python3
"""Arithmetic for the thirty-sixth run's invented examples (Ch25, 26, 33, 36, 40). Offline, seeded, no API calls."""
import random, math, statistics as st

def ch25():
    IN, OUT, READ, WRITE = 3.0, 15.0, 0.30, 3.75   # placeholder $ per million
    H, BRIEF, N, STEPS, STEP_IN, STEP_OUT = 30_000, 2_000, 4, 6, 1_500, 400
    def run(start):
        # one subagent: first call writes the start context, later calls read it and add step tokens
        total = 0.0; ctx = start
        for s in range(STEPS):
            if s == 0: total += ctx * WRITE / 1e6
            else: total += (ctx) * READ / 1e6 + STEP_IN * IN / 1e6
            if s == 0: total += STEP_IN * IN / 1e6
            ctx += STEP_IN + STEP_OUT
            total += STEP_OUT * OUT / 1e6
        return total
    full = N * run(H); brief = N * run(BRIEF) + H * IN / 1e6 * 0 + 800 * OUT / 1e6 * N  # parent writes 800-token brief each
    return dict(per_sub_full=run(H), per_sub_brief=run(BRIEF), team_full=full, team_brief=brief, saving=1 - brief / full)

def ch26(seed=26):
    rnd = random.Random(seed); out = {}
    mean_daily = 400.0
    for cap_mult in (1.5, 2.0, 3.0):
        trips = 0; months = 2000
        for _ in range(months):
            for d in range(30):
                # daily spend lognormal sigma 0.45, mean 400; weekend factor 0.5 on 8 of 30 days
                f = 0.5 if d % 7 in (5, 6) else 1.0
                x = rnd.lognormvariate(math.log(mean_daily) - 0.45**2 / 2, 0.45) * f
                if x > cap_mult * mean_daily: trips += 1
        out[cap_mult] = trips / months
    return out

def ch33(seed=33):
    rnd = random.Random(seed); n = 20000
    use = sorted(rnd.lognormvariate(0, 1.2) for _ in range(n))  # relative usage
    tot = sum(use); res = {}
    for pct in (90, 95, 99):
        cap = use[int(n * pct / 100)]
        over = sum(max(0, u - cap) for u in use)
        res[pct] = dict(cap=cap, share_users_over=sum(u > cap for u in use) / n, cost_share_removed=over / tot)
    top1 = sum(use[-n // 100:]) / tot; top10 = sum(use[-n // 10:]) / tot
    return res, top1, top10

def ch36():
    pool = 90_000.0
    teams = {"Search": (520, 60), "Support": (260, 40), "Sales ops": (120, 25), "Platform": (100, 15)}  # (usage k-requests, headcount)
    ut = sum(v[0] for v in teams.values()); ht = sum(v[1] for v in teams.values())
    return {k: (pool * v[0] / ut, pool * v[1] / ht) for k, v in teams.items()}, ut, ht

def ch40():
    q1_vol, q1_rate = 10.0, 0.0300  # billion tokens, $ per thousand
    q1 = 300_000.0
    q2 = 346_500.0
    return None

if __name__ == "__main__":
    print("CH25", ch25()); print("CH26", ch26()); print("CH33", ch33()); print("CH36", ch36())
