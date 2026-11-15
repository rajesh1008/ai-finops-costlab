#!/usr/bin/env python3
"""Run 39 lab. REAL calls. Same prompt repeated N times at default temperature on haiku-4-5: how much does billed output vary? Three prompts (closed, semi-open, open), 10 repeats each, max_tokens 400."""
import os, sys, json, time, statistics as st
from pathlib import Path
M = "claude-haiku-4-5-20251001"
PROMPTS = {
 "closed": "In one sentence, what is a cache read token?",
 "semi": "Explain in a short paragraph why retries raise the cost per solved task.",
 "open": "List the ways a team could cut the cost of an LLM support bot, with a line on each.",
}
N = 10
OUT = Path(__file__).resolve().parents[1] / "runs" / "output-variance-2026-11-13.jsonl"
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("no key")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    for k, p in PROMPTS.items():
        for i in range(N):
            r = cl.messages.create(model=M, max_tokens=400, messages=[{"role": "user", "content": p}])
            rows.append({"prompt": k, "rep": i, "in": r.usage.input_tokens, "out": r.usage.output_tokens, "stop": r.stop_reason}); time.sleep(0.3)
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]
    for k in PROMPTS:
        o = [r["out"] for r in rows if r["prompt"] == k]; cut = sum(r["stop"] == "max_tokens" for r in rows if r["prompt"] == k)
        print(k, "n", len(o), "in", rows[[r["prompt"] for r in rows].index(k)]["in"], "min", min(o), "max", max(o), "mean", round(st.mean(o), 1), "sd", round(st.stdev(o), 1), "cv", round(st.stdev(o) / st.mean(o), 3), "truncated", cut)
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 else main()
