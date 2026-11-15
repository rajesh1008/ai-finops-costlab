#!/usr/bin/env python3
"""48th run offline arithmetic for Ch4, 21, 25, 28, 30, 32, 37, 38, 46. Every input is invented and labelled so in the chapters."""
import math
def breakeven_success(cost_per_attempt, value): return cost_per_attempt / value                     # Ch4
def seq_calls(p, n): return (1 - (1 - p) ** n) / p                                                  # Ch25 expected calls, stop at first accepted answer
def seq_success(p, n): return 1 - (1 - p) ** n
def policy_net(blocked_bad, saved_each, false_blocks, lost_each): return blocked_bad * saved_each - false_blocks * lost_each   # Ch32
def finetune_payback_months(train, host_month, base_month, tuned_token_month):                      # Ch21
    saving = base_month - host_month - tuned_token_month
    return math.inf if saving <= 0 else train / saving
def sample_size(p0, delta, z_a=1.645, z_b=0.842):                                                   # Ch28, one-sided 5 percent, 80 percent power
    p1 = p0 - delta; pb = (p0 + p1) / 2
    return math.ceil(((z_a * math.sqrt(2 * pb * (1 - pb)) + z_b * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2) / delta ** 2)
def commit_effective_discount(commit, list_discount, used_list_value):                              # Ch30: commit is in discounted dollars
    used_disc = used_list_value * (1 - list_discount); paid = max(commit, used_disc)
    return 1 - paid / used_list_value
def fte_payback(salary_loaded, spend, saved_share): return salary_loaded / (spend * saved_share) if spend * saved_share else math.inf   # Ch37
def tco(build_year1, build_run, buy_fee, buy_integration, years=3):                                 # Ch38
    return build_year1 + build_run * (years - 1), buy_integration + buy_fee * years
def delay_cost(daily, detect_days, fix_days): return daily * (detect_days + fix_days)              # Ch46
def main():
    print("Ch4 break-even success rate: cost/attempt vs value")
    for c, v in ((0.40, 4.0), (1.20, 4.0), (2.00, 4.0), (3.20, 4.0)): print(f"  cost {c:.2f} value {v:.2f} -> {breakeven_success(c, v):.0%}")
    print("Ch25 sequential escalation, expected calls and success, p per worker")
    for p in (0.5, 0.7, 0.9):
        print(" p", p, [(n, round(seq_calls(p, n), 2), round(seq_success(p, n), 3)) for n in (1, 2, 3, 5)])
    print("Ch32 policy net", policy_net(420, 3.10, 35, 14.0), policy_net(420, 3.10, 120, 14.0))
    print("Ch21 payback months", [round(finetune_payback_months(18000, h, 9000, t), 1) for h, t in ((2400, 600), (3600, 600), (5400, 600))])
    print("Ch28 n per arm", [(d, sample_size(0.85, d)) for d in (0.10, 0.05, 0.03)])
    print("Ch30 effective discount", [round(commit_effective_discount(800_000, 0.20, u), 4) for u in (1_250_000, 1_000_000, 800_000, 600_000)])
    print("Ch37 payback FTE years", [round(fte_payback(190_000, s, 0.05), 2) for s in (1_000_000, 3_000_000, 10_000_000)])
    print("Ch38 TCO", tco(260_000, 140_000, 90_000, 40_000), tco(260_000, 140_000, 150_000, 40_000))
    print("Ch46 delay cost", delay_cost(1800, 9, 2), delay_cost(1800, 1, 2))
if __name__ == "__main__": main()
