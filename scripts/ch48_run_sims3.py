#!/usr/bin/env python3
"""48th run offline arithmetic, part three: Ch2, 5, 6, 11, 12, 14. All inputs invented and labelled in the chapters."""
def task_cost(tin, vis, think, pin, pout): return (tin * pin + (vis + think) * pout) / 1e6               # Ch2: thinking tokens billed as output
def unmetered(total, bypass_share): return total * bypass_share                                           # Ch5
def alloc(shares_basis, pool): t = sum(shares_basis.values()); return {k: pool * v / t for k, v in shares_basis.items()}   # Ch6
def cost_per_verified(total_cost, outcomes_claimed, verify_rate): return total_cost / (outcomes_claimed * verify_rate)    # Ch11
def tier_margin(price, users, cost_each): return [(u, price - c, (price - c) * u) for u, c in zip(users, cost_each)]       # Ch12
def per_thousand(spend, volume): return spend / volume * 1000                                             # Ch14
def main():
    A = task_cost(2000, 300, 0, 3.0, 15.0); B = task_cost(2000, 300, 4000, 3.0, 15.0); C = task_cost(2000, 300, 0, 1.0, 5.0)
    print("Ch2", round(A, 4), round(B, 4), round(C, 4), "B vs A", round(B / A, 2))
    print("Ch5", unmetered(240000, 0.07), unmetered(240000, 0.15))
    print("Ch6 by requests", alloc({"a": 600000, "b": 300000, "c": 100000}, 50000), "by tokens", alloc({"a": 600000 * 500, "b": 300000 * 2000, "c": 100000 * 4000}, 50000))
    print("Ch11", round(cost_per_verified(9800, 4000, 0.82), 2), round(9800 / 4000, 2))
    print("Ch12", tier_margin(30.0, (7000, 2500, 450, 50), (4.0, 14.0, 41.0, 190.0)))
    print("Ch14", per_thousand(180000, 600000), per_thousand(95000, 210000))
if __name__ == "__main__": main()
