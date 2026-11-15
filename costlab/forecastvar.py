"""Chapter 45: how wide a forecast interval must be when per-call cost varies run to run, and whether an interval built from a short history covers what happened.
Pure functions; the lab (scripts/forecast_variance_lab.py) supplies real per-call output-token counts."""
import random, statistics as st

def call_cost(tin, tout, usd_in, usd_out): return tin / 1e6 * usd_in + tout / 1e6 * usd_out

def cv(xs):
    m = st.fmean(xs)
    return (st.pstdev(xs) / m) if m else 0.0

def bootstrap_total_interval(history, n_calls, draws=2000, lo=0.05, hi=0.95, seed=1):
    """Interval for the total cost of `n_calls` future calls, resampling per-call costs from `history` with replacement."""
    rng = random.Random(seed)
    tots = sorted(sum(rng.choices(history, k=n_calls)) for _ in range(draws))
    return tots[int(lo * draws)], tots[int(hi * draws) - 1]

def point_total(history, n_calls): return st.fmean(history) * n_calls

def normal_total_interval(history, n_calls, z=1.645):
    m, s = st.fmean(history), st.pstdev(history)
    half = z * s * n_calls ** 0.5
    return m * n_calls - half, m * n_calls + half

def coverage(groups, hist_n, future_n, method, trials=400, seed=7):
    """groups: list of per-call cost lists drawn from one population (e.g. per template). Each trial draws `hist_n` calls as history and `future_n` calls as the future month at random
    (without overlap, within one population), builds the interval, and checks the realised total. Returns (share covered, mean width / mean actual)."""
    rng = random.Random(seed); hit = 0; w = []
    for _ in range(trials):
        pool = rng.choice(groups)
        idx = rng.sample(range(len(pool)), min(len(pool), hist_n + future_n)); h = [pool[i] for i in idx[:hist_n]]; f = [pool[i] for i in idx[hist_n:]]
        lo, hi = method(h, len(f)); act = sum(f)
        hit += lo <= act <= hi; w.append((hi - lo) / act if act else 0)
    return hit / trials, st.fmean(w)

def volume_error_decomposition(forecast_volume, actual_volume, forecast_rate, actual_rate):
    """Split total variance into volume and rate parts: dV*r_f, V_a*dr (order stated, so the parts sum exactly)."""
    vol = (actual_volume - forecast_volume) * forecast_rate
    rate = actual_volume * (actual_rate - forecast_rate)
    return vol, rate, vol + rate
