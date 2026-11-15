#!/usr/bin/env python3
"""Chapter 10 simulation (SYNTHETIC, not a measurement). One year of daily spend with a weekday pattern ($4,000 weekday, $1,500 weekend, multiplicative lognormal noise sigma 0.08) and six injected runaways. Compares four alert rules on false alerts per year and on how many runaways they catch on the day. Seed fixed so the output reproduces."""
import random, statistics, math, json, sys
def make(seed=10, days=365, sigma=0.08, n_run=6, mult=1.6):
    r = random.Random(seed); base = []
    for d in range(days):
        b = 4000 if d % 7 < 5 else 1500
        base.append(b * math.exp(r.gauss(0, sigma)))
    spots = sorted(r.sample([d for d in range(60, days) if d % 7 < 5], n_run))
    x = list(base)
    for d in spots: x[d] = base[d] * mult
    return x, spots
def rule_mean7(x, d, pct=0.20): return x[d] > (1 + pct) * (sum(x[d-7:d]) / 7)
def rule_same_weekday(x, d, pct=0.20):
    m = statistics.median([x[d-7], x[d-14], x[d-21], x[d-28]]); return x[d] > (1 + pct) * m
def rule_same_weekday_floor(x, d, pct=0.20, floor=500):
    m = statistics.median([x[d-7], x[d-14], x[d-21], x[d-28]]); return x[d] > (1 + pct) * m and x[d] - m > floor
def rule_same_weekday_pct10(x, d): return rule_same_weekday(x, d, 0.10)
RULES = {"mean of last 7 days, +20%": rule_mean7, "median same weekday x4, +20%": rule_same_weekday,
         "same weekday, +20% and over $500": rule_same_weekday_floor, "same weekday, +10%": rule_same_weekday_pct10}
def evaluate(x, spots):
    out = {}
    for name, f in RULES.items():
        fired = [d for d in range(28, len(x)) if f(x, d)]
        caught = [d for d in spots if d in fired]
        false = [d for d in fired if d not in spots]
        out[name] = {"alerts": len(fired), "false": len(false), "caught": len(caught), "of": len(spots)}
    return out
if __name__ == "__main__":
    x, spots = make()
    print("SYNTHETIC year, seed 10, runaway days:", spots)
    for k, v in evaluate(x, spots).items(): print(f"{k:38s} alerts {v['alerts']:3d} false {v['false']:3d} caught {v['caught']}/{v['of']}")
