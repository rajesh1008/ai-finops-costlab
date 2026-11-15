#!/usr/bin/env python3
"""Chapter 2 lab: where do thinking tokens show up in usage? Real calls to claude-haiku-4-5.

Compares output_tokens reported by the API with the token count of the visible answer text
(counted with the token-counting endpoint). The gap is thinking spend billed as output.
"""
import os, sys, json
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter

MODEL = "claude-haiku-4-5-20251001"
LOG = Path(__file__).resolve().parents[1] / "runs" / "reasoning-2026-11-10.jsonl"
Q = ("A customer was charged $49 per seat for 14 seats, then given a 15 percent discount on the total, "
     "then refunded for 3 seats at the discounted per-seat price. What is the net amount charged? "
     "Give the number and one sentence.")

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    client = Anthropic()
    meter = Meter(client, LOG, product="reasoning-lab")
    for label, extra in (("no-thinking", {}), ("thinking-2048", {"thinking": {"type": "enabled", "budget_tokens": 2048}})):
        msg = meter.call(model=MODEL, session_id=label, step=1, feature="reasoning-lab",
                         max_tokens=4000, messages=[{"role": "user", "content": Q}], **extra)
        visible = "".join(b.text for b in msg.content if b.type == "text")
        n_visible = client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": visible}]).input_tokens
        kinds = [b.type for b in msg.content]
        print(f"{label}: output_tokens_billed={msg.usage.output_tokens} visible_text_tokens~{n_visible} blocks={kinds}")
        print("answer:", visible.strip()[:160].replace("\n", " "))

if __name__ == "__main__":
    main()
