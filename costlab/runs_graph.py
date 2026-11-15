"""Chapter 7: roll call-grain cost up a run graph (session -> run -> subrun) and summarise the tail."""
from dataclasses import dataclass, field
from collections import defaultdict
import random
import statistics


@dataclass
class Call:
    call_id: str
    session_id: str
    run_id: str
    parent_run_id: str | None
    cost: float
    kind: str = "model"          # model, tool, retry


def rollup(calls: list[Call]) -> dict[str, float]:
    """Cost of each run including every descendant run. A run's own calls plus its children's."""
    own = defaultdict(float)
    children = defaultdict(set)
    for c in calls:
        own[c.run_id] += c.cost
        if c.parent_run_id:
            children[c.parent_run_id].add(c.run_id)
    memo: dict[str, float] = {}

    def total(r: str, seen=()) -> float:
        if r in seen:
            raise ValueError(f"cycle at {r}")
        if r not in memo:
            memo[r] = own[r] + sum(total(k, seen + (r,)) for k in children[r])
        return memo[r]
    return {r: total(r) for r in set(own) | set(children)}


def session_costs(calls: list[Call]) -> dict[str, float]:
    out = defaultdict(float)
    for c in calls:
        out[c.session_id] += c.cost
    return dict(out)


def percentile(xs: list[float], p: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def tail_summary(costs: list[float]) -> dict:
    s = sorted(costs, reverse=True)
    total = sum(s)
    top = max(1, round(0.03 * len(s)))
    return {"sessions": len(s), "total": total, "mean": total / len(s),
            "median": statistics.median(s), "p95": percentile(s, 0.95), "p99": percentile(s, 0.99),
            "max": s[0], "top3pct_share": sum(s[:top]) / total}


def synthetic_day(n_sessions=4000, seed=7, loop_rate=0.01, loop_mult=60.0) -> list[float]:
    """SYNTHETIC. Lognormal session cost (median about 9 cents) plus a small share of runaway sessions."""
    rng = random.Random(seed)
    out = []
    for _ in range(n_sessions):
        c = rng.lognormvariate(mu=-2.4, sigma=0.9)
        if rng.random() < loop_rate:
            c *= loop_mult * rng.uniform(0.5, 1.5)
        out.append(c)
    return out
