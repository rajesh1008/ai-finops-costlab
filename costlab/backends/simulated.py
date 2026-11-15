"""Simulated ("assumed cost") backend: no model is called. Token counts are assumptions supplied by the lab;
dollars come from costlab.price_table. Includes an Anthropic-style cache TTL model (5m or 1h, refreshed on read)."""
from __future__ import annotations

from costlab import price_table

TTL_MIN = {"5m": 5.0, "1h": 60.0}


def simulate_session(model: str, gaps_min: list[float], *, prefix_tokens: int, suffix_tokens: int,
                     output_tokens: int, ttl: str | None = "5m", batch: bool = False) -> dict:
    """Cost of 1 + len(gaps_min) calls sharing a prefix. ttl=None means no caching.
    A call within `ttl` of the previous call reads (and refreshes) the cache; otherwise it writes again."""
    calls = 1 + len(gaps_min)
    writes = reads = 0
    total = 0.0
    for i in range(calls):
        if ttl is None:
            c = price_table.cost_usd(model, input_tokens=prefix_tokens + suffix_tokens, output_tokens=output_tokens, batch=batch)
        else:
            hit = i > 0 and gaps_min[i - 1] <= TTL_MIN[ttl]
            reads += hit; writes += (not hit)
            c = price_table.cost_usd(model, input_tokens=suffix_tokens, output_tokens=output_tokens,
                                     cache_write_tokens=0 if hit else prefix_tokens,
                                     cache_read_tokens=prefix_tokens if hit else 0, write_ttl=ttl, batch=batch)
        total += c["total"]
    return {"calls": calls, "writes": writes, "reads": reads, "total_usd": total}


def breakeven_gap_table(model: str, gaps: list[float], *, prefix_tokens: int, suffix_tokens: int,
                        output_tokens: int, calls: int = 100) -> list[dict]:
    """For a steady gap between calls, compare no cache, 5m TTL and 1h TTL over `calls` calls."""
    rows = []
    for g in gaps:
        gl = [g] * (calls - 1)
        r = {"gap_min": g}
        for name, ttl in (("none", None), ("5m", "5m"), ("1h", "1h")):
            r[name] = simulate_session(model, gl, prefix_tokens=prefix_tokens, suffix_tokens=suffix_tokens,
                                       output_tokens=output_tokens, ttl=ttl)["total_usd"]
        r["cheapest"] = min(("none", "5m", "1h"), key=lambda k: r[k])
        rows.append(r)
    return rows


def provenance(model: str) -> dict:
    return price_table.provenance("simulated", model)
