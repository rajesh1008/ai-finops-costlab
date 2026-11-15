#!/usr/bin/env python3
"""Chapter 13 lab. REAL calls. How much does the billed output of one identical prompt vary from call to call? Same 12 prompts as billed_output_lab, 5 repeats, two models, default sampling, max_tokens 4000."""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
sys.path.insert(0, str(Path(__file__).parent))
from billed_output_lab import P, MODELS
OUT = Path(__file__).resolve().parents[1] / "runs" / "repeat-spread-lab-2026-11-12.jsonl"
def one(a):
    cl, m, kind, pi, rep = a
    x = cl.messages.create(model=m, max_tokens=4000, messages=[{"role": "user", "content": P[kind][pi]}])
    return {"model": m, "kind": kind, "p": pi, "rep": rep, "input": x.usage.input_tokens, "out": x.usage.output_tokens, "stop": x.stop_reason}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, k, i, r) for m in MODELS for k in P for i in range(2) for r in range(5)]
    rows = []
    def safe(j):
        try: return one(j)
        except Exception as e: return {"model": j[1], "kind": j[2], "p": j[3], "rep": j[4], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
if __name__ == "__main__": main()
