#!/usr/bin/env python3
"""Chapter 18 lab. REAL calls to claude-haiku-4-5 (minimum cacheable prompt 4,096 tokens). Four layouts, 6 calls each, sequential.
A: no cache_control. B: breakpoint at end of the static prefix, question after it. C: timestamp inside the prefix (failure injection).
D: breakpoint on the block that holds the per-call question. Each condition has its own salt line so conditions never share a cache."""
import os, sys, json, time
from pathlib import Path
from datetime import datetime, timezone
from anthropic import Anthropic
from costlab.gateway import Meter
from scripts_common import handbook  # noqa
MODEL = "claude-haiku-4-5-20251001"
RUNS = Path(__file__).resolve().parents[1] / "runs"
LOG = RUNS / "cache-layout-2026-11-10.jsonl"
QS = ["Summarise clause 12 in one sentence.", "What reference does clause 40 use?", "How many days is the retention window in clause 77?",
      "Which tier does clause 100 cover?", "State clause 150 briefly.", "What reference does clause 3 use?"]
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    if LOG.exists(): LOG.unlink()
    meter = Meter(Anthropic(), LOG, product="cache-layout-lab")
    cc = {"type": "ephemeral"}
    for cond in "ABCD":
        for i, q in enumerate(QS, 1):
            salt = f"Layout {cond}, run 2026-11-10 (salt)."
            base = salt + "\n" + handbook()
            stamp = f"Current time: {datetime.now(timezone.utc).isoformat()}\n"
            if cond == "A":
                system = [{"type": "text", "text": base}]; msgs = [{"role": "user", "content": q}]
            elif cond == "B":
                system = [{"type": "text", "text": base, "cache_control": cc}]; msgs = [{"role": "user", "content": q}]
            elif cond == "C":
                system = [{"type": "text", "text": stamp + base, "cache_control": cc}]; msgs = [{"role": "user", "content": q}]
            else:
                system = [{"type": "text", "text": base}]
                msgs = [{"role": "user", "content": [{"type": "text", "text": q, "cache_control": cc}]}]
            for attempt in range(3):
                try:
                    meter.call(model=MODEL, session_id=f"{cond}-{i}", step=1, feature=f"layout-{cond}", max_tokens=60, system=system, messages=msgs); break
                except Exception as e:
                    print("retry", cond, i, str(e)[:80], flush=True); time.sleep(4)
            else: raise SystemExit("call kept failing")
            time.sleep(1.5)
    print("done")
if __name__ == "__main__": main()
