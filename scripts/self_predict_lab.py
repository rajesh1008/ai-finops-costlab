#!/usr/bin/env python3
"""Chapter 7 / Chapter 24 lab. REAL calls. Does a model predict its own billed output tokens before it answers? 12 prompts (same as billed_output_lab), 3 repeats, two models. Step 1 asks for an integer estimate of the billed output tokens the task would use; step 2 runs the task and records billed output. Prompts are mine; the idea follows a published study of self-prediction in coding agents, at toy scale."""
import os, sys, json, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
sys.path.insert(0, str(Path(__file__).parent))
from billed_output_lab import P, MODELS
OUT = Path(__file__).resolve().parents[1] / "runs" / "self-predict-lab-2026-11-12.jsonl"
ASK = "Before doing the task below, estimate how many output tokens you would bill to complete it, counting any hidden reasoning as well as the visible answer. Reply with a single integer and nothing else.\n\nTask: "
def one(a):
    cl, m, kind, pi, rep = a
    pr = cl.messages.create(model=m, max_tokens=4000, messages=[{"role": "user", "content": ASK + P[kind][pi]}])
    t = "".join(b.text for b in pr.content if b.type == "text")
    nums = re.findall(r"\d[\d,]*", t)
    pred = int(nums[-1].replace(",", "")) if nums else None
    x = cl.messages.create(model=m, max_tokens=4000, messages=[{"role": "user", "content": P[kind][pi]}])
    return {"model": m, "kind": kind, "p": pi, "rep": rep, "pred": pred, "pred_call_out": pr.usage.output_tokens, "actual": x.usage.output_tokens, "stop": x.stop_reason}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, k, i, r) for m in MODELS for k in P for i in range(2) for r in range(3)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
if __name__ == "__main__": main()
