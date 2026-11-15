"""Arithmetic behind the forty-fourth run's added sections. Every input is invented and labelled as such in the book,
except the session-replay numbers, which come from runs/session-replay-summary-2026-11-13.txt (real API calls)."""
import math

def session_input(first, per_turn, turns):
    """Input tokens summed over a session that resends history: first prompt, then +per_turn each turn."""
    return turns * first + per_turn * turns * (turns - 1) // 2

def folded_input(first, per_turn, turns, fold_at, carried):
    """Same, but at fold_at the history is replaced by a summary of `carried` tokens (then grows per_turn again)."""
    tot = 0
    for t in range(1, turns + 1):
        if t <= fold_at:
            tot += first + per_turn * (t - 1)
        else:
            tot += carried + per_turn * (t - fold_at - 1) + (first - 0)
    return tot

def session_cost(inp, out, pin=1.0, pout=5.0):
    return (inp * pin + out * pout) / 1e6

def delayed_regression(save_per_day, loss_per_day, start_day, detect_lag, horizon):
    """A lever saves from day 0; a quality regression begins at start_day and costs loss_per_day until it is
    detected (detect_lag days later) and rolled back. Returns net, gross saving, regression cost."""
    gross = save_per_day * horizon
    reg_days = min(detect_lag, horizon - start_day)
    loss = loss_per_day * reg_days
    return gross - loss, gross, loss

def log_error(est, truth):
    return abs(math.log10(est / truth))

def handoff_tokens(agents, own_work, passed, mode):
    """Chain of agents. 'full' passes the whole transcript so far; 'summary' passes a fixed summary of `passed` tokens."""
    tot, carried = 0, 0
    for i in range(agents):
        if mode == "full":
            tot += carried + own_work
            carried += own_work
        else:
            tot += (passed if i else 0) + own_work
    return tot

def forecast_buffer(monthly, horizon, pct_err_sd):
    """Mean absolute pct error of a naive growth forecast given monthly spend history; returns buffer sized at ~1.65 sd."""
    growth = [monthly[i + 1] / monthly[i] - 1 for i in range(len(monthly) - 1)]
    g = sum(growth) / len(growth)
    proj = monthly[-1] * (1 + g) ** horizon
    return g, proj, proj * (1 + 1.65 * pct_err_sd)

def record_storage(rows_per_day, bytes_row, days, price_gb_month):
    gb = rows_per_day * bytes_row * days / 1e9
    return gb, gb * price_gb_month

def batch_breakeven(price, discount, delay_h, cost_per_hour_delay):
    """Batch saves price*discount per request; delay costs delay_h*cost_per_hour_delay per request. Net per request."""
    return price * discount - delay_h * cost_per_hour_delay

def autonomy_threshold(p_err, cost_err, review_cost, catch):
    """Expected cost per item auto-approved vs reviewed (reviewer catches `catch` of errors)."""
    auto = p_err * cost_err
    rev = review_cost + p_err * (1 - catch) * cost_err
    return auto, rev, review_cost / (catch * cost_err)  # last is break-even error rate

def outcome_price(cost_per_attempt, success, margin):
    """Price per successful outcome that holds a gross margin when failures are unbilled."""
    cpo = cost_per_attempt / success
    return cpo, cpo / (1 - margin)

def sampled_body_cost(req_per_day, body_bytes, sample, days, price_gb_month):
    gb = req_per_day * body_bytes * sample * days / 1e9
    return gb, gb * price_gb_month

def tokenizer_breakeven(price_ratio, token_ratio):
    """New model costs price_ratio of old per token and counts token_ratio times the tokens (input only).
    Returns the cost ratio and the price ratio at which cost is equal."""
    return price_ratio * token_ratio, 1 / token_ratio

def bucket_burst(rate_per_min, bucket, spike_rate, spike_min):
    """Token bucket: starts full; returns minutes until empty under spike (rate in $ per min), or None."""
    net = spike_rate - rate_per_min
    if net <= 0: return None
    t = bucket / net
    return t if t <= spike_min else None

def cap_share(costs, cap):
    capped = [c for c in costs if c > cap]
    saved = sum(c - cap for c in capped)
    return len(capped) / len(costs), saved, sum(costs)

def value_breakeven(cost_per_req, p_success, value_success):
    return p_success * value_success - cost_per_req

def shadow_output_heavy(n, in_tok, out_tok, pin, pout, think_mult):
    base = n * (in_tok * pin + out_tok * pout) / 1e6
    shadow = n * (in_tok * pin + out_tok * think_mult * pout) / 1e6
    return base, shadow

if __name__ == "__main__":
    print("== Ch7 session growth (measured 57 first, +117/turn)")
    for n in (12, 20, 40, 80):
        i = session_input(57, 117, n); print(n, i, round(session_cost(i, n * 80), 5), "input share", round(i / (i + n * 80 * 5), 3))
    print("measured plain", 8411.3, "folded", 4435.0, "saving", round(1 - 4435 / 8411.3, 4), "cost", 0.01321, 0.00914, round(1 - 0.00914 / 0.01321, 4))
    print("fold model (carried 108-57=51?)", folded_input(57, 117, 12, 6, 51))
    print("plain avg per turn", round(8411.3 / 12, 1), "last turn vs first", round(1341 / 57, 2))
    print("20-turn customer sessions 1M/mo: plain", session_cost(session_input(300, 250, 20), 20 * 200) * 1e6)
    print("== Ch43 delayed regression")
    for lag in (3, 14, 30):
        print(lag, delayed_regression(900, 2400, 10, lag, 60))
    print("== Ch47 log errors", [round(log_error(e, 120000), 3) for e in (60000, 100000, 130000, 1200000)])
    print("== Ch25 handoff", [handoff_tokens(a, 3000, 600, m) for a in (3, 5, 8) for m in ("full", "summary")])
    print("== Ch13", forecast_buffer([41000, 44500, 47800, 53000, 56200, 61500], 3, 0.08))
    print("== Ch8", record_storage(2_000_000, 900, 395, 0.023), record_storage(2_000_000, 900, 30, 0.023))
    print("== Ch20", batch_breakeven(0.010, 0.5, 6, 0.0004), batch_breakeven(0.010, 0.5, 6, 0.001))
    print("== Ch16", autonomy_threshold(0.04, 25.0, 0.60, 0.85), autonomy_threshold(0.01, 25.0, 0.60, 0.85))
    print("== Ch15", outcome_price(0.18, 0.72, 0.6), outcome_price(0.18, 0.55, 0.6))
    print("== Ch5", sampled_body_cost(5_000_000, 6000, 1.0, 30, 0.023), sampled_body_cost(5_000_000, 6000, 0.02, 30, 0.023))
    print("== Ch35", tokenizer_breakeven(0.10 / 1.0, 1.335), tokenizer_breakeven(0.8, 1.339))
    print("== Ch26", bucket_burst(2.0, 120.0, 14.0, 30), bucket_burst(2.0, 120.0, 6.0, 30), bucket_burst(2.0, 120.0, 6.0, 40))
    costs = [4]*700 + [9]*200 + [25]*70 + [60]*25 + [210]*5
    print("== Ch33", cap_share(costs, 50), cap_share(costs, 100))
    print("== Ch4", value_breakeven(0.12, 0.6, 0.30), value_breakeven(0.12, 0.6, 0.15))
    print("== Ch28", shadow_output_heavy(20000, 1800, 300, 1.0, 5.0, 4.0))

def fold_net(plain_tail, folded_tail, summary_in, summary_out, summary_tokens, carried_assumed, remaining, pin=1.0, pout=5.0):
    """Net input-token saving (in dollars) from a model-written summary at the fold point.
    plain_tail/folded_tail: input tokens of the later turns without/with the fold (measured, folded run used `carried_assumed` tokens of summary)."""
    saved = (sum(plain_tail) - sum(folded_tail) - (summary_tokens - carried_assumed) * remaining) * pin / 1e6
    call = (summary_in * pin + summary_out * pout) / 1e6
    return saved, call, saved - call

def fold_break_even_turns(history, summary_tokens, summary_out, pin=1.0, pout=5.0):
    """Remaining turns after which a model-written summary call pays for itself."""
    return (history * pin + summary_out * pout) / ((history - summary_tokens) * pin)

def fixed_cost_break_even(build_cost, saving_per_req, monthly_req):
    return build_cost / (saving_per_req * monthly_req)
