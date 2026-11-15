#!/usr/bin/env python3
"""48th run offline arithmetic, part two: Ch8, 10, 17, 19, 20, 22, 24, 27. All inputs invented and labelled in the chapters."""
import math
def store_gb(records_per_day, bytes_each, days): return records_per_day * bytes_each * days / 1e9               # Ch8
def store_cost(gb, per_gb_month, months=1): return gb * per_gb_month * months
def false_alerts_per_year(k, per_day=1):                                                                          # Ch10, one-sided normal tail
    tail = 0.5 * math.erfc(k / math.sqrt(2)); return tail * per_day * 365
def cascade_cost(c_small, c_large, accept): return c_small + (1 - accept) * c_large                              # Ch17
def cascade_breakeven_accept(c_small, c_large): return c_small / c_large
def diet_saving(tokens_cut, price_per_m, calls_per_month): return tokens_cut * price_per_m * calls_per_month / 1e6  # Ch19
def blended_batch(cost_sync, batch_share, batch_discount): return cost_sync * (1 - batch_share * batch_discount)  # Ch20
def expected_attempts(f, cap): return cap if f >= 1 else (1 - f ** cap) / (1 - f)                                # Ch22: failure prob f per attempt
def agent_input_tokens(n, s0, g): return n * s0 + g * n * (n - 1) // 2                                             # Ch24
def ladder_cost(shares, costs): return sum(s * c for s, c in zip(shares, costs))                                  # Ch27
def main():
    gb = store_gb(2_000_000, 1200, 400); print("Ch8 GB", gb, "hot $/mo", store_cost(gb, 0.023), "cold", store_cost(gb, 0.004))
    print("Ch10 false alerts/yr", [(k, round(false_alerts_per_year(k), 1)) for k in (2, 3, 4)])
    print("Ch17", [(a, round(cascade_cost(0.002, 0.020, a), 4)) for a in (0.5, 0.7, 0.9)], cascade_breakeven_accept(0.002, 0.020))
    print("Ch19", diet_saving(1800, 3.0, 400_000), diet_saving(1800, 1.0, 400_000))
    print("Ch20", [(s, blended_batch(60000, s, 0.5)) for s in (0.1, 0.3, 0.5)])
    print("Ch22", [(f, round(expected_attempts(f, 4), 3)) for f in (0.1, 0.3, 0.6, 1.0)])
    print("Ch24", [(n, agent_input_tokens(n, 3000, 1500)) for n in (5, 10, 20)])
    print("Ch27", ladder_cost((0.7, 0.2, 0.1), (0.020, 0.004, 0.0005)), ladder_cost((0.4, 0.4, 0.2), (0.020, 0.004, 0.0005)))
if __name__ == "__main__": main()
