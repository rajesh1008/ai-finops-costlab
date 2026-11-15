#!/usr/bin/env python3
"""Real API smoke test. Reads ANTHROPIC_API_KEY from the environment. Never prints it."""

import os
from datetime import datetime, timezone
from anthropic import Anthropic
from costlab.estimate import estimate_usd
from costlab.records import CostRecord

MODEL = "claude-haiku-4-5-20251001"


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=40,
        messages=[{"role": "user", "content": "Reply with exactly: costlab-ok"}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content)
    usage = msg.usage
    estimated = estimate_usd(
        f"anthropic:{MODEL}",
        usage.input_tokens,
        usage.output_tokens,
        getattr(usage, "cache_read_input_tokens", 0) or 0,
        getattr(usage, "cache_creation_input_tokens", 0) or 0,
    )
    record = CostRecord(
        record_id="smoke-1",
        occurred_at=datetime.now(timezone.utc),
        vendor="anthropic",
        model=msg.model,
        product="costlab-smoke",
        feature="api-connectivity",
        environment="lab",
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        estimated_cost_usd=round(estimated, 8),
        source="smoke-test",
        notes=f"text={text!r}",
    )
    print(record.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
