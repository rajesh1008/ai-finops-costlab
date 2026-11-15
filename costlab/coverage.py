"""Gateway coverage of an invoice period, and what a log gap puts at risk.

Spend is not flat across a month that grows. With a monthly growth rate g, day d of the
month weighs g ** (d / days). The gap's share of the month's dollars is the weight of the
missing days over the weight of all days. The growth model is an assumption: pass 1.0 for flat.
"""
from datetime import date, timedelta
from typing import Iterable


def days_in(start: date, end: date) -> list[date]:
    n = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(n)]


def covered_days(record_dates: Iterable[date]) -> set[date]:
    return set(record_dates)


def gap_report(period_start: date, period_end: date, record_dates: Iterable[date],
               monthly_growth: float = 1.0, invoice_total: float = 0.0) -> dict:
    days = days_in(period_start, period_end)
    have = covered_days(record_dates)
    missing = [d for d in days if d not in have]
    n = len(days)
    weight = {d: monthly_growth ** (i / n) for i, d in enumerate(days)}
    total_w = sum(weight.values())
    miss_w = sum(weight[d] for d in missing)
    share = miss_w / total_w if total_w else 0.0
    return {"days": n, "missing_days": len(missing), "missing_from": missing[0] if missing else None,
            "day_share": len(missing) / n, "dollar_share": share, "usd_at_risk": share * invoice_total}
