#!/usr/bin/env python3
"""Chapter 2 lab (issue 13): ten trials per condition of the seat-refund question. Real calls, Haiku 4.5.

Correct answer: $458.15. A trial is correct if the visible text contains 458.15.
"""
import os, sys, re
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter

MODEL = "claude-haiku-4-5-20251001"
LOG = Path(__file__).resolve().parents[1] / "runs" / "reasoning-trials-2026-11-10.jsonl"
Q = ("A customer was charged $49 per seat for 14 seats, then given a 15 percent discount on the total, "
     "then refunded for 3 seats at the discounted per-seat price. What is the net amount charged? "
     "Give the number and one sentence.")
N = 10

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="reasoning-trials")
    for label, extra in (("no-thinking", {}), ("thinking-2048", {"thinking": {"type": "enabled", "budget_tokens": 2048}})):
        ok, toks = 0, []
        for i in range(1, N + 1):
            msg = meter.call(model=MODEL, session_id=f"{label}-{i}", step=1, feature="reasoning-trials",
                             max_tokens=4000, messages=[{"role": "user", "content": Q}], **extra)
            text = "".join(b.text for b in msg.content if b.type == "text")
            good = "458.15" in text.replace(",", "")
            ok += good; toks.append(msg.usage.output_tokens)
            print(f"{label} {i}: correct={good} billed_output={msg.usage.output_tokens}", flush=True)
        print(f"SUMMARY {label}: correct {ok}/{N} billed_output min={min(toks)} median={sorted(toks)[N//2]} max={max(toks)} mean={sum(toks)/N:.0f}")

if __name__ == "__main__":
    main()
