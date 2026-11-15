"""Dated Anthropic list prices for keyless lab modes (local-model and simulated).

Source: https://docs.anthropic.com/en/docs/about-claude/pricing (Model pricing and
Batch processing tables), read in full on 16 November 2026 (Asia/Calcutta).

USD per million tokens. Batch is 50% of input and output; the page says batch and
prompt-caching discounts combine, so cache multipliers are applied to the batch base
when both are used. Haiku 5.5 has a long-prompt tier above 100,000 prompt tokens.

These prices are what an Anthropic invoice WOULD show for the given token counts.
Figures computed with them are calculations, never invoice measurements.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

PRICING_DATE = date(2026, 11, 16)
PRICING_SOURCE = "https://docs.anthropic.com/en/docs/about-claude/pricing"
BATCH_DISCOUNT = 0.50


@dataclass(frozen=True)
class ModelPrice:
    input: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float
    output: float
    long_threshold: int | None = None      # prompt tokens above which `long` applies
    long: "ModelPrice | None" = None


_H55_LONG = ModelPrice(0.50, 0.625, 1.00, 0.05, 2.50)

PRICES: dict[str, ModelPrice] = {
    "claude-opus-5-5": ModelPrice(4.00, 5.00, 8.00, 0.20, 20.00),
    "claude-opus-5": ModelPrice(5.00, 6.25, 10.00, 0.50, 25.00),
    "claude-opus-4-8": ModelPrice(5.00, 6.25, 10.00, 0.50, 25.00),
    "claude-opus-4-7": ModelPrice(5.00, 6.25, 10.00, 0.50, 25.00),
    "claude-opus-4-6": ModelPrice(5.00, 6.25, 10.00, 0.50, 25.00),
    "claude-opus-4-5": ModelPrice(5.00, 6.25, 10.00, 0.50, 25.00),
    "claude-sonnet-5-5": ModelPrice(2.00, 2.50, 4.00, 0.10, 10.00),
    "claude-sonnet-5": ModelPrice(2.00, 2.50, 4.00, 0.20, 10.00),
    "claude-sonnet-4-6": ModelPrice(3.00, 3.75, 6.00, 0.30, 15.00),
    "claude-sonnet-4-5": ModelPrice(3.00, 3.75, 6.00, 0.30, 15.00),
    "claude-haiku-5-5": ModelPrice(0.10, 0.125, 0.20, 0.01, 0.50, long_threshold=100_000, long=_H55_LONG),
    "claude-haiku-4-5": ModelPrice(1.00, 1.25, 2.00, 0.10, 5.00),
}
ALIASES = {"claude-haiku-4-5-20251001": "claude-haiku-4-5"}


def price_for(model: str) -> ModelPrice:
    key = ALIASES.get(model, model)
    if key not in PRICES:
        raise KeyError(f"no dated price for {model!r}; add it from {PRICING_SOURCE}")
    return PRICES[key]


def cost_usd(model: str, *, input_tokens: int = 0, output_tokens: int = 0,
             cache_write_tokens: int = 0, cache_read_tokens: int = 0,
             write_ttl: str = "5m", batch: bool = False) -> dict:
    """Line-item cost for one request. `input_tokens` are uncached input tokens only."""
    if write_ttl not in ("5m", "1h"):
        raise ValueError("write_ttl must be '5m' or '1h'")
    for v in (input_tokens, output_tokens, cache_write_tokens, cache_read_tokens):
        if v < 0:
            raise ValueError("token counts must be non-negative")
    p = price_for(model)
    prompt = input_tokens + cache_write_tokens + cache_read_tokens
    if p.long_threshold is not None and prompt > p.long_threshold and p.long is not None:
        p = p.long
    f = BATCH_DISCOUNT if batch else 1.0
    w = p.cache_write_5m if write_ttl == "5m" else p.cache_write_1h
    lines = {
        "input": input_tokens * p.input * f / 1e6,
        "cache_write": cache_write_tokens * w * f / 1e6,
        "cache_read": cache_read_tokens * p.cache_read * f / 1e6,
        "output": output_tokens * p.output * f / 1e6,
    }
    lines["total"] = sum(lines.values())
    return lines


def provenance(mode: str, priced_as: str, local_model: str | None = None) -> dict:
    """Header every keyless output must carry."""
    if mode not in ("local-model", "simulated"):
        raise ValueError("mode must be 'local-model' or 'simulated'")
    d = {"mode": mode, "priced_as": priced_as, "pricing_date": PRICING_DATE.isoformat(),
         "pricing_source": PRICING_SOURCE,
         "note": ("Token counts, latency and prefix-cache hits measured on a small open model run locally; "
                  "dollars calculated from published Anthropic list prices. Not an Anthropic invoice measurement."
                  if mode == "local-model" else
                  "Pure calculation from published Anthropic list prices and stated assumptions. No model was called.")}
    if local_model:
        d["local_model"] = local_model
    return d
