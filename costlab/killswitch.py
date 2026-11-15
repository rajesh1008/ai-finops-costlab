"""Chapter 44: controls on a runaway agent loop, and the time-to-stop arithmetic of a night incident.
`run_loop` is client-agnostic: `step(history)` returns (input_tokens, output_tokens, tool_call or None, text). The tool always fails (the lab's strict-error condition).
Controls: none (only the lab's hard step ceiling), breaker (same call repeated `limit` times), cap (dollar cap per run, worst-case reserved before each step via budgets.Authority)."""
from costlab.budgets import Authority, Blocked, Breaker, worst_case_cost

def run_loop(step, usd_in, usd_out, control="none", ceiling=30, cap_usd=0.02, breaker_limit=3, max_out=300):
    cost, steps, stopped, reason = 0.0, 0, False, "finished"
    auth = Authority({"run": cap_usd}, mode="hard_gate") if control == "cap" else None
    br = Breaker(limit=breaker_limit, errors=10 ** 9) if control == "breaker" else None
    hist = []
    for n in range(ceiling):
        res = None
        if auth:
            prompt_est = sum(h[0] for h in hist[-1:]) or 800
            try: res = auth.reserve(["run"], worst_case_cost(prompt_est + 200, max_out, usd_in, usd_out))
            except Blocked: stopped, reason = True, "cap"; break
        tin, tout, call, text = step(hist)
        actual = tin / 1e6 * usd_in + tout / 1e6 * usd_out
        cost += actual; steps += 1; hist.append((tin, tout, call, text))
        if auth: auth.commit(res, actual)
        if call is None: break
        if br and br.observe(call[0], call[1], error=True): stopped, reason = True, "breaker"; break
    else:
        reason = "ceiling"
    return {"cost": cost, "steps": steps, "stopped": stopped, "reason": reason}

def time_to_stop(detect_min, page_min, decide_min, act_min): return detect_min + page_min + decide_min + act_min

def incident_cost(rate_per_min, minutes_to_stop, ramp_min=0.0):
    """Spend accrued before the stop. The rate ramps linearly from zero over `ramp_min` then holds."""
    if ramp_min <= 0: return rate_per_min * minutes_to_stop
    if minutes_to_stop <= ramp_min: return rate_per_min * minutes_to_stop ** 2 / (2 * ramp_min)
    return rate_per_min * ramp_min / 2 + rate_per_min * (minutes_to_stop - ramp_min)
