"""Chapter 12: customer-level gross margin under three price models. SYNTHETIC customers; every parameter is an assumption."""
import random
from dataclasses import dataclass


@dataclass
class Customer:
    cid: int
    seats: int
    tasks: int          # tasks in the month
    cost_per_task: float


def customers(n=400, seed=12, median_tasks_per_seat=40, sigma=1.1, base_cost=0.55):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        seats = rnd.choice([5, 10, 10, 20, 25, 50])
        t = int(seats * median_tasks_per_seat * rnd.lognormvariate(0, sigma))
        out.append(Customer(i, seats, t, base_cost * rnd.lognormvariate(0, 0.25)))
    return out


def cost(c: Customer):
    return c.tasks * c.cost_per_task


def seat_price(c, per_seat=50.0):
    return c.seats * per_seat


def seat_with_allowance(c, per_seat=50.0, allowance_per_seat=50, overage=1.20):
    extra = max(0, c.tasks - allowance_per_seat * c.seats)
    return c.seats * per_seat + extra * overage


def per_task(c, price=1.50):
    return c.tasks * price


def summary(cs, price_fn):
    rev = [price_fn(c) for c in cs]; cst = [cost(c) for c in cs]
    gm = [(r - k) / r for r, k in zip(rev, cst)]
    neg = sum(1 for g in gm if g < 0)
    order = sorted(range(len(cs)), key=lambda i: -cst[i])
    top = order[: max(1, len(cs) // 10)]
    return {"revenue": sum(rev), "cost": sum(cst), "gm": 1 - sum(cst) / sum(rev), "neg_share": neg / len(cs),
            "median_gm": sorted(gm)[len(gm) // 2], "p10_gm": sorted(gm)[len(gm) // 10],
            "top_decile_cost_share": sum(cst[i] for i in top) / sum(cst),
            "top_decile_rev_share": sum(rev[i] for i in top) / sum(rev),
            "loss_dollars": -sum(r - k for r, k in zip(rev, cst) if r < k)}
