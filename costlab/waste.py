"""Chapters 7 and 9: retry waste, tool-registry overhead and human-wait cost. All inputs are SYNTHETIC or ASSUMED and labelled by callers."""
import random
from dataclasses import dataclass

IN_RATE = 1.00 / 1e6     # placeholder USD per input token (lab rate card, 10 Nov 2026)
OUT_RATE = 5.00 / 1e6
READ_RATE = 0.10 / 1e6
WRITE_RATE = 1.25 / 1e6


def call_cost(inp: int, out: int, cached_read: int = 0, cache_write: int = 0) -> float:
    return inp * IN_RATE + out * OUT_RATE + cached_read * READ_RATE + cache_write * WRITE_RATE


@dataclass
class RetryResult:
    tasks: int
    outcomes: int
    calls: int
    first_try_cost: float
    total_cost: float

    @property
    def waste_share(self) -> float:
        return 1 - self.first_try_cost / self.total_cost if self.total_cost else 0.0


def simulate_retries(p_fail: float, max_attempts: int, tasks: int = 5000, seed: int = 11,
                     ctx_tokens: int = 6000, out_tokens: int = 400, correlated: float = 0.0) -> RetryResult:
    """Each task makes one call. A failed call (timeout, malformed output) is retried up to max_attempts total.
    Every attempt is billed in full (input and output) because the failure is detected after the tokens are spent.
    `correlated` is the chance a retry fails again for the same cause (a bad prompt does not heal)."""
    rng = random.Random(seed)
    unit = call_cost(ctx_tokens, out_tokens)
    outcomes = calls = 0
    total = first = 0.0
    for _ in range(tasks):
        first += unit
        ok = False
        failing_cause = rng.random() < p_fail
        for attempt in range(max_attempts):
            calls += 1
            total += unit
            if not failing_cause:
                ok = True
                break
            if attempt + 1 < max_attempts and rng.random() >= correlated:
                failing_cause = rng.random() < p_fail   # transient: fresh draw
        outcomes += ok
    return RetryResult(tasks, outcomes, calls, first, total)


def tool_overhead(n_tools_exposed: int, tokens_per_tool: int, steps: int, fixed_overhead: int = 496) -> dict:
    """Per-session input tokens spent only to describe tools. tokens_per_tool is ASSUMED by the caller."""
    per_step = fixed_overhead + n_tools_exposed * tokens_per_tool
    tokens = per_step * steps
    return {"per_step": per_step, "session_tokens": tokens, "usd_uncached": tokens * IN_RATE,
            "usd_cached": per_step * WRITE_RATE + (steps - 1) * per_step * READ_RATE}


def human_wait_cost(prefix_tokens: int, waits_min: list[float], ttl_min: float = 5.0, out_tokens: int = 150) -> dict:
    """A session pauses for a person between calls. If the pause exceeds the cache lifetime the next call
    re-writes the prefix (write rate), else it reads it (read rate). ttl_min is ASSUMED by the caller."""
    cost = call_cost(0, out_tokens, 0, prefix_tokens)   # first call writes the prefix
    expired = 0
    for w in waits_min:
        if w > ttl_min:
            expired += 1
            cost += call_cost(0, out_tokens, 0, prefix_tokens)
        else:
            cost += call_cost(0, out_tokens, prefix_tokens, 0)
    always_hot = call_cost(0, out_tokens, 0, prefix_tokens) + len(waits_min) * call_cost(0, out_tokens, prefix_tokens, 0)
    return {"calls": len(waits_min) + 1, "expired": expired, "cost": cost, "if_never_expired": always_hot}
