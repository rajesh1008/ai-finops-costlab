"""Chapter 15: what an outcome-priced agent earns, and what a buyer really pays per true resolution.
SYNTHETIC inputs; every parameter is an assumption stated in the script that calls this."""
import random


def billed_outcomes(n, p_true, q_assumed, recontact, rnd):
    """n conversations. A conversation is truly resolved with probability p_true. An unresolved one is still
    billed as an 'assumed resolution' with probability q_assumed (customer leaves without asking again).
    A billed unresolved one is deducted later with probability `recontact` (customer returns to the thread)."""
    true_res = billed = deducted = 0
    for _ in range(n):
        if rnd.random() < p_true:
            true_res += 1; billed += 1
        elif rnd.random() < q_assumed:
            billed += 1
            if rnd.random() < recontact:
                billed -= 1; deducted += 1
    return {"n": n, "true": true_res, "billed": billed, "deducted": deducted}


def buyer_price_per_true(price, r):
    return price * r["billed"] / max(1, r["true"])


def breakeven_resolution_rate(cost_per_conv, price):
    """Minimum resolution rate at which price per outcome covers inference cost of every conversation,
    resolved or not. Above 1.0 means no rate can cover it."""
    return cost_per_conv / price


def vendor_margin(n, cost_per_conv, price, res_rate, fixed=0.0):
    rev = n * res_rate * price + fixed
    cost = n * cost_per_conv
    return (rev - cost) / rev if rev else float("nan")


def six_month_variance(n=10_000, cost_per_conv=0.31, res_rate=0.55, drift=0.0, sigma=0.04, seed=15, months=12):
    """Monthly vendor gross margin under four price models when resolution rate wobbles. SYNTHETIC."""
    rnd = random.Random(seed)
    rows = []
    for m in range(months):
        rr = min(0.95, max(0.1, res_rate + drift * m + rnd.gauss(0, sigma)))
        seat_rev = 6000.0
        out_rev = n * rr * 0.99
        hyb_rev = 2000.0 + n * rr * 0.60
        cost = n * cost_per_conv
        rows.append((m + 1, rr, (seat_rev - cost) / seat_rev, (out_rev - cost) / out_rev, (hyb_rev - cost) / hyb_rev))
    return rows
