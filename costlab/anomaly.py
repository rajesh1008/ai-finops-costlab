"""Chapter 10: anomaly detectors over the Chapter 9 dataset. SYNTHETIC data. Simple on purpose."""
import statistics
from collections import defaultdict
from .views import generate, daily


def trailing_median_alert(series: dict[int, float], window=7, pct=0.5, min_days=7):
    """Alert on day d when cost exceeds trailing median by more than pct. Returns list of days."""
    out = []
    days = sorted(series)
    for i, d in enumerate(days):
        if i < min_days:
            continue
        base = statistics.median(series[x] for x in days[max(0, i - window):i])
        if series[d] > base * (1 + pct):
            out.append(d)
    return out


def static_threshold_alert(series, ceiling):
    return [d for d in sorted(series) if series[d] > ceiling]


def session_cap_stop(rows, session, cap_usd):
    """Gateway rule: refuse the next call once the session's spend reaches cap_usd. Returns (step_stopped, usd_spent)."""
    spent = 0.0
    for r in sorted((r for r in rows if r.session == session), key=lambda r: r.step):
        if spent >= cap_usd:
            return r.step, spent
        spent += r.cost
    return None, spent


def scale_traffic(rows, days_from, factor):
    """SYNTHETIC planned launch: from day `days_from` every row's cost is multiplied by factor (more traffic, same shape)."""
    from dataclasses import replace
    return [replace(r, cost=r.cost * factor) if r.day >= days_from else r for r in rows]


def anomaly_cost_pct(rows_with_flag_days, total):
    return rows_with_flag_days / total
