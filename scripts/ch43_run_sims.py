"""Arithmetic behind the forty-third run's added sections. All inputs are invented, labelled in the book."""
import json

def ladder_expected(p_ok, costs):
    """Expected cost per request on a ladder where rung i is tried if all earlier rungs failed.
    p_ok[i] = probability rung i succeeds when tried; costs[i] = cost of trying it."""
    exp, reach = 0.0, 1.0
    for p, c in zip(p_ok, costs):
        exp += reach * c
        reach *= (1 - p)
    return exp, reach  # reach = share that falls off the bottom

def shadow_cache(n, prefix_tokens, in_price, write_mult=1.25, read_mult=0.1, ttl_gap_ok=True):
    """Candidate input cost for n shadow requests with and without a cached prefix (price per MTok)."""
    plain = n * prefix_tokens * in_price / 1e6
    cached = (prefix_tokens * in_price * write_mult + (n - 1) * prefix_tokens * in_price * read_mult) / 1e6
    return plain, cached

def judge_sample_cost(n_per_day, rate, judge_cost, regress_rate, detect_n):
    """Days to see detect_n regressions at a sampled rate, and judge spend until then."""
    per_day = n_per_day * rate
    days = detect_n / (per_day * regress_rate)
    return per_day, days, days * per_day * judge_cost

def commit_breakeven(list_price, discount, utilisation):
    """Committed spend is paid whether used or not. Effective price per used unit = list*(1-d)/u."""
    return list_price * (1 - discount) / utilisation, 1 - discount

def policy_eval(req_per_day, eval_ms, hosts_cost_month, prevented_per_month):
    return hosts_cost_month / (req_per_day * 30) * 1000, prevented_per_month / hosts_cost_month

def team_breakeven(fte_cost, saving_share, spend):
    return fte_cost / saving_share, spend * saving_share

def tco(build_eng, build_maint, buy_fee, buy_integr, years=3):
    return build_eng + build_maint * years, buy_integr + buy_fee * years

def dread_rate(base, mult, n):
    return 1 - (1 - base) ** n

if __name__ == "__main__":
    out = {}
    # Ch27: three-rung ladder, invented
    out["ch27_a"] = ladder_expected([0.97, 0.90, 1.0], [0.0120, 0.0030, 0.0000])
    out["ch27_b"] = ladder_expected([0.97, 0.90, 0.60, 1.0], [0.0120, 0.0030, 0.0004, 0.0])
    out["ch27_retry"] = ladder_expected([0.97, 0.97, 0.90, 1.0], [0.0120, 0.0120, 0.0030, 0.0])
    # Ch28
    out["ch28"] = shadow_cache(28000, 6000, 1.00)
    out["ch28_gap"] = shadow_cache(28000, 6000, 1.00, ttl_gap_ok=False)
    # Ch29
    out["ch29"] = judge_sample_cost(80000, 0.05, 0.0021, 0.01, 30)
    out["ch29b"] = judge_sample_cost(80000, 0.01, 0.0021, 0.01, 30)
    # Ch31
    out["ch31"] = [commit_breakeven(1.0, 0.20, u) for u in (1.0, 0.9, 0.8, 0.75)]
    # Ch32
    out["ch32"] = policy_eval(200000, 3, 900, 14000)
    # Ch37
    out["ch37"] = team_breakeven(180000, 0.05, 3_000_000)
    out["ch37b"] = team_breakeven(180000, 0.05, 1_200_000)
    # Ch38
    out["ch38"] = tco(240000, 90000, 84000, 30000)
    # Ch39
    out["ch39"] = [dread_rate(0.02, 1, n) for n in (1, 5, 10, 20)]
    print(json.dumps(out, indent=1))
