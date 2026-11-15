"""Chapter 10 growth: replay alert rules over a simulated month whose per-run costs are REAL (the 120 dependent-lookup runs of the Chapter 24 chain lab, placeholder rates).
Volume (Poisson, flat across hours), the incident (a share of runs replaced by draws from the dearest 13 runs, which are the 16-step-cap runs) and its timing are SYNTHETIC or ASSUMED."""
import numpy as np

def month(pool, tail, runs_per_hour=125, hours=720, inc_start=None, inc_extra=0.0, seed=0):
    """Return (hourly_spend, hourly_runs_over_ceiling_count_inputs) as arrays. After inc_start (hour index), each run is replaced with probability inc_extra by a draw from `tail`."""
    rng = np.random.default_rng(seed); pool = np.asarray(pool); tail = np.asarray(tail)
    n = rng.poisson(runs_per_hour, hours); spend = np.zeros(hours); hot = np.zeros(hours, dtype=int)
    p99 = np.quantile(pool, 0.99)
    for h in range(hours):
        c = rng.choice(pool, n[h])
        if inc_start is not None and h >= inc_start and inc_extra > 0:
            m = rng.random(n[h]) < inc_extra; c[m] = rng.choice(tail, m.sum())
        spend[h] = c.sum(); hot[h] = int((c >= p99).sum())
    return spend, hot

def first_day_alert_trailing_median(daily, window=7, pct=0.5, min_days=7, start=0):
    for i in range(max(min_days, start), len(daily)):
        base = np.median(daily[max(0, i - window):i])
        if daily[i] > base * (1 + pct): return i
    return None

def first_hour_alert_hourly(spend, window=168, mult=1.5, min_hours=168, start=0):
    """Alert when an hour's spend exceeds mult times the median of the trailing `window` hours."""
    for h in range(max(min_hours, start), len(spend)):
        if spend[h] > mult * np.median(spend[h - window:h]): return h
    return None

def first_hour_alert_hot(hot, k, min_hours=0, start=0):
    """Alert when at least k runs in one hour cost at least the 99th percentile of ordinary runs."""
    for h in range(max(min_hours, start), len(hot)):
        if hot[h] >= k: return h
    return None
