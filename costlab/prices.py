"""Dated placeholder prices. Not market benchmarks.

As-of date: 9 November 2026. Replace from vendor pages before any published arithmetic.
"""

from datetime import date

PRICE_AS_OF = date(2026, 11, 9)

# USD per million tokens. Placeholder values used only in labs.
PLACEHOLDER_USD_PER_MTIOK = {
    "anthropic:claude-haiku-4-5-20251001": {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
    # Added 10 November 2026 from the vendor pricing page opened in full that day (platform.claude.com/docs/en/about-claude/pricing).
    "anthropic:claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_read": 0.01, "cache_write": 0.125},   # prompts up to 100k tokens
    "anthropic:claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "anthropic:claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.10, "cache_write": 2.50},
}

CURRENCY = "USD"

# Added 10 November 2026 after reading the vendor pricing page the same day.
# Haiku 4.5 rates matched the page: $1 input, $5 output, 1.25x cache write, 0.1x cache read.
