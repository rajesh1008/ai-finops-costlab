#!/usr/bin/env python3
"""Chapter 2 and 18 lab: measure what a prompt-cache write and read do to the usage fields.

Real calls to claude-haiku-4-5. A synthetic policy handbook of several thousand tokens is the
cached prefix. Five identical-prefix calls with different questions; the first writes, the rest read.
"""
import os, sys
from pathlib import Path
from anthropic import Anthropic
from costlab.gateway import Meter

MODEL = "claude-haiku-4-5-20251001"
LOG = Path(__file__).resolve().parents[1] / "runs" / "cache-experiment-2026-11-10.jsonl"

def handbook() -> str:
    clauses = []
    for i in range(1, 161):
        clauses.append(f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account "
                       f"owner, record reference FS-{1000 + i * 13}, and confirm the retention window of "
                       f"{30 + (i % 12) * 15} days before describing any export or deletion procedure.")
    return "Fieldstone Analytics support handbook (synthetic).\n" + "\n".join(clauses)

QUESTIONS = ["Summarise clause 12 in one sentence.", "What reference does clause 40 use?",
             "How many days is the retention window in clause 77?", "Which tier does clause 100 cover?",
             "State clause 150 briefly."]

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="cache-lab")
    system = [{"type": "text", "text": handbook(), "cache_control": {"type": "ephemeral"}}]
    for i, q in enumerate(QUESTIONS, 1):
        meter.call(model=MODEL, session_id=f"cache-{i}", step=1, feature="cache-lab", max_tokens=80,
                   system=system, messages=[{"role": "user", "content": q}])

if __name__ == "__main__":
    main()
