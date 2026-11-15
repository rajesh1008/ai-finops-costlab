"""Chapter 9: three dashboard views computed from ONE call-grain dataset. SYNTHETIC data generator included."""
import random
from collections import defaultdict
from dataclasses import dataclass
from .waste import call_cost

PRODUCTS = {"support-agent": ("support", 0.52), "nl-query": ("analytics", 0.22), "knowledge-assistant": ("platform", 0.26)}


@dataclass
class Row:
    day: int
    product: str
    team: str | None        # None means unowned
    session: str
    step: int
    inp: int
    out: int
    cread: int
    cwrite: int
    cost: float
    outcome: bool           # step closes an accepted outcome


def generate(days: int = 30, per_day: int = 400, seed: int = 21, spike_day: int = 19) -> list[Row]:
    """SYNTHETIC. Sessions of 1-12 steps. Day `spike_day` has one runaway session of 90 steps in support-agent.
    About 8 percent of rows carry no team (an unowned credential)."""
    rng = random.Random(seed)
    rows: list[Row] = []
    sid = 0
    names = list(PRODUCTS)
    weights = [PRODUCTS[n][1] for n in names]
    for d in range(1, days + 1):
        for _ in range(per_day):
            sid += 1
            prod = rng.choices(names, weights)[0]
            team = PRODUCTS[prod][0]
            if rng.random() < 0.08:
                team = None
            steps = min(12, 1 + int(rng.expovariate(0.45)))
            ctx = 1500
            for s in range(1, steps + 1):
                out = int(rng.lognormvariate(5.2, 0.5))
                new = int(rng.lognormvariate(6.0, 0.5))
                inp = new
                cread = ctx if s > 1 else 0
                cwrite = 0 if s > 1 else ctx
                cost = call_cost(inp, out, cread, cwrite)
                rows.append(Row(d, prod, team, f"s{sid}", s, inp, out, cread, cwrite, cost,
                                outcome=(s == steps and rng.random() < 0.78)))
                ctx += new + out
        if d == spike_day:
            sid += 1
            ctx = 1500
            for s in range(1, 91):
                out, new = 600, 2500
                rows.append(Row(d, "support-agent", "support", f"s{sid}", s, new, out,
                                ctx if s > 1 else 0, 0 if s > 1 else ctx, call_cost(new, out, ctx if s > 1 else 0, 0 if s > 1 else ctx), False))
                ctx += new + out
    return rows


def engineer_view(rows, session):
    """Per-step decomposition by token class for one session."""
    out = []
    for r in rows:
        if r.session == session:
            out.append((r.step, r.inp * 1e-6, r.out * 5e-6, r.cread * 1e-7, r.cwrite * 1.25e-6, r.cost))
    return out


def top_sessions(rows, n=3):
    t = defaultdict(float)
    for r in rows:
        t[r.session] += r.cost
    return sorted(t.items(), key=lambda kv: -kv[1])[:n]


def finance_view(rows):
    by_team: dict[str, float] = defaultdict(float)
    for r in rows:
        by_team[r.team or "UNOWNED"] += r.cost
    total = sum(by_team.values())
    return {"total": total, "by_team": dict(by_team), "coverage": 1 - by_team.get("UNOWNED", 0) / total}


def board_view(rows):
    spend = defaultdict(float)
    outs = defaultdict(int)
    for r in rows:
        spend[r.product] += r.cost
        outs[r.product] += r.outcome
    return {p: (spend[p], outs[p], spend[p] / outs[p] if outs[p] else None) for p in spend}


def daily(rows):
    d = defaultdict(float)
    for r in rows:
        d[r.day] += r.cost
    return dict(d)


def invoice_view_daily(rows, days):
    """What a dashboard built from the monthly invoice shows: the month total spread evenly over the days."""
    tot = sum(r.cost for r in rows)
    return {d: tot / days for d in range(1, days + 1)}


def otel_to_cr2(input_tokens_incl_cached: int, cache_read: int, cache_write: int) -> int:
    """The working-draft OpenTelemetry usage counters report input INCLUDING cached tokens, with cache read and write
    as subsets. Cost Record cr-2 keeps input_tokens as uncached only. Convert, and refuse impossible rows."""
    uncached = input_tokens_incl_cached - cache_read - cache_write
    if uncached < 0:
        raise ValueError("cache subsets exceed total input: producer bug")
    return uncached


def priced_both_ways(inp_incl: int, read: int, write: int, out: int) -> tuple[float, float]:
    """(correct, naive). The naive dashboard prices the OTel input counter at the full input rate AND prices cache again."""
    from .waste import call_cost
    correct = call_cost(otel_to_cr2(inp_incl, read, write), out, read, write)
    naive = call_cost(inp_incl, out, read, write)
    return correct, naive
