#!/usr/bin/env python3
"""Chapter 44 follow-up (nineteenth run), REAL calls. The always-has_more paginated tool of killswitch_pages_lab.py, no control, ceiling 20 steps, per-step input and output tokens RECORDED.
8 runs per model (claude-haiku-4-5-20251001, claude-haiku-5-5 thinking disabled) = 16 runs, about 320 calls. Output runs/loop-growth-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
sys.path.insert(0, str(Path(__file__).resolve().parent))
from killswitch_pages_lab import make_step, MODELS
OUT = Path(__file__).resolve().parents[1] / "runs" / "loop-growth-lab-2026-11-11.json"
def one(cl, m, t):
    model, kw, _ = MODELS[m]; step = make_step(cl, model, kw); hist = []
    for n in range(20):
        try: tin, tout, call, text = step(hist)
        except RuntimeError: return {"m": m, "trial": t, "calls": [(h[0], h[1]) for h in hist], "error": True}
        hist.append((tin, tout, call, text))
        if call is None: break
    return {"m": m, "trial": t, "calls": [(h[0], h[1]) for h in hist], "error": False, "ended_with_text": hist[-1][2] is None}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(m, t) for m in MODELS for t in range(8)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(lambda j: one(cl, *j), jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(r["error"] for r in res))
if __name__ == "__main__": main()
