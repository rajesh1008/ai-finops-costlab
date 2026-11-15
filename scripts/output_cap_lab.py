#!/usr/bin/env python3
"""Chapter 27 and 33 lab. REAL calls. What does a max_tokens cap do to billed output and to whether the caller gets any visible answer? Same 12 prompts as billed_output_lab, four caps, two models, one call per cell."""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
sys.path.insert(0, str(Path(__file__).parent))
from billed_output_lab import P, MODELS
CAPS = [50, 150, 400, 2000]
OUT = Path(__file__).resolve().parents[1] / "runs" / "output-cap-lab-2026-11-12.jsonl"
def one(a):
    cl, m, kind, pi, cap = a
    x = cl.messages.create(model=m, max_tokens=cap, messages=[{"role": "user", "content": P[kind][pi]}])
    text = "".join(b.text for b in x.content if getattr(b, "type", "") == "text")
    return {"model": m, "kind": kind, "p": pi, "cap": cap, "input": x.usage.input_tokens, "out": x.usage.output_tokens,
            "stop": x.stop_reason, "visible_chars": len(text), "blocks": [b.type for b in x.content]}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, k, i, c) for m in MODELS for k in P for i in range(2) for c in CAPS]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"model": j[1], "kind": j[2], "p": j[3], "cap": j[4], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
if __name__ == "__main__": main()
