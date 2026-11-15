#!/usr/bin/env python3
"""Chapter 26 lab (twenty-first run). REAL calls. A max_tokens ceiling as a blunt budget: 10 tasks, 4 ceilings, 3 repeats, 2 models.
Each task asks for an explanation that must end with a line 'DECISION: yes' or 'DECISION: no'. A truncated answer lacks the line. Tasks are mine. Never prints the key."""
import os, sys, json, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "maxtokens-lab-2026-11-11.jsonl"
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
CAPS = [100, 200, 400, 800]
TASKS = ["a team's weekly cost report shows a 9 percent rise with flat traffic", "a cache hit rate fell from 62 to 41 percent after a prompt edit", "a nightly batch job now takes 31 hours of a 24 hour window", "a support agent's average steps per run rose from 5 to 8", "a vendor offers 15 percent off for a 12 month commitment on a bill that varies 40 percent month to month", "an embeddings line doubled while documents grew 5 percent", "a retry rate of 12 percent on one tool", "a product with 71 percent gross margin has one customer at negative margin", "a forecast missed by 22 percent in the month a new model launched", "a team asks to bypass the gateway for a latency test"]
def one(a):
    cl, m, cap, ti, rep = a
    x = cl.messages.create(model=m, max_tokens=cap, messages=[{"role": "user", "content": f"Explain, for a finance partner, whether to investigate this: {TASKS[ti]}. Give the reasoning, then end with exactly one final line: DECISION: yes or DECISION: no."}])
    t = "".join(b.text for b in x.content if b.type == "text")
    return {"model": m, "cap": cap, "task": ti, "rep": rep, "out": x.usage.output_tokens, "in": x.usage.input_tokens, "stop": x.stop_reason, "has_decision": bool(re.search(r"DECISION:\s*(yes|no)\s*\**\s*$", t.strip(), re.I))}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, c, t, r) for m in MODELS for c in CAPS for t in range(10) for r in range(3)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
    for m in MODELS:
        for c in CAPS:
            q = [x for x in res if x["model"] == m and x["cap"] == c]
            print(m, c, "n", len(q), "hit-ceiling", sum(x["stop"] == "max_tokens" for x in q), "has-decision", sum(x["has_decision"] for x in q), "mean out %.0f" % (sum(x["out"] for x in q)/len(q)))
if __name__ == "__main__": main()
