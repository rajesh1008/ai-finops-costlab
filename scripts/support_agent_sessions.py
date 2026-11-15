#!/usr/bin/env python3
"""Chapter 5 and 7 lab: run a toy support agent through the Meter and log every call.

Real calls to claude-haiku-4-5. The ticket data is synthetic. One scenario injects a failure:
the lookup tool keeps answering 'index busy, retry', which a naive agent obeys until the cap.
Never prints the key.
"""
import os, sys
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter

MODEL = "claude-haiku-4-5-20251001"
LOG = Path(__file__).resolve().parents[1] / "runs" / "meter-2026-11-10.jsonl"
MAX_STEPS = 8

TOOLS = [{
    "name": "lookup_ticket_history",
    "description": "Return the customer's previous support tickets as short summaries.",
    "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}},
                     "required": ["customer_id"]},
}]

SYSTEM = ("You are the Fieldstone Analytics support agent (a synthetic company). Answer in at most "
          "three sentences. Use lookup_ticket_history only when the question depends on past tickets.")

SCENARIOS = [
    ("reset-1", "How do I reset my dashboard password?", "ok"),
    ("reset-2", "I forgot my password for the analytics portal, what are the steps?", "ok"),
    ("export-1", "Can I export a report to CSV?", "ok"),
    ("export-2", "Which export formats does a scheduled report support?", "ok"),
    ("billing-1", "I was charged twice in September. Check my earlier tickets, customer cust-4471.", "ok"),
    ("billing-2", "My refund request from last month never arrived, customer cust-1180. What happened to it?", "ok"),
    ("billing-3", "Look at all my past tickets, customer cust-9033, and tell me if my invoice dispute is still open.", "busy"),
    ("billing-4", "Check my history for customer cust-2210 and tell me why I keep being billed for a closed workspace.", "busy"),
    # Failure injection: the same busy tool, but the system prompt demands a verified answer.
    ("loop-1", "Check my history for customer cust-7781 and tell me if my invoice dispute is still open.", "strict"),
    ("loop-2", "Look up customer cust-3350 tickets and confirm whether my refund was issued.", "strict"),
]
STRICT_SUFFIX = (" Never answer a billing question without a successful ticket lookup. "
                 "If the lookup fails, call it again until it succeeds.")

def tool_result(mode: str, step: int) -> str:
    if mode in ("busy", "strict"):
        return "ERROR: ticket index busy, please retry the lookup."
    return ("Ticket 8812: duplicate charge on invoice, refund issued, closed. "
            "Ticket 8790: workspace closure confirmed, billing stop requested.")

def run_session(meter, sid, question, mode):
    messages = [{"role": "user", "content": question}]
    for step in range(1, MAX_STEPS + 1):
        msg = meter.call(model=MODEL, session_id=sid, step=step, feature="support-chat",
                         tenant="tenant-demo", team="support-agent", max_tokens=300,
                         system=SYSTEM + (STRICT_SUFFIX if mode == "strict" else ""), tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": msg.content})
        uses = [b for b in msg.content if b.type == "tool_use"]
        if not uses:
            return step, "resolved"
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id, "content": tool_result(mode, step)} for b in uses]})
    return MAX_STEPS, "capped"

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists():
        LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="support-agent")
    for sid, q, mode in SCENARIOS:
        steps, outcome = run_session(meter, sid, q, mode)
        print(f"{sid}: steps={steps} outcome={outcome}")

if __name__ == "__main__":
    main()
