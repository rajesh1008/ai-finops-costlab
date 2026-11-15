#!/usr/bin/env python3
"""Chapter 17 follow-up lab (nineteenth run), REAL calls. 40 harder SYNTHETIC billing problems (costlab/cascade_hard.py, seed 19). Arms: H45 x2, H55 x2, S46 x1 answering in prose (max_tokens 400),
and EXPR: claude-haiku-5-5 (thinking disabled) asked for one arithmetic expression only, evaluated by the harness. 40 x (2+2+1+1) = 240 calls. Output runs/cascade-hard-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.cascade_hard import make_hard
OUT = Path(__file__).resolve().parents[1] / "runs" / "cascade-hard-lab-2026-11-11.json"
MODELS = {"H45": ("claude-haiku-4-5-20251001", {}), "H55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}}), "S46": ("claude-sonnet-4-6", {}), "EXPR": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
PLAN = [("H45", 2), ("H55", 2), ("S46", 1), ("EXPR", 1)]
SUF = " Give the number and one sentence."
EXPR = " Reply with ONE arithmetic expression only, using numbers and the operators + - * / and parentheses, that evaluates to the final amount. No words, no dollar signs, no equals sign."
def one(cl, job):
    p, k, j = job; model, kw = MODELS[k]
    for att in range(4):
        try:
            x = cl.messages.create(model=model, max_tokens=400, messages=[{"role": "user", "content": p["q"] + (EXPR if k == "EXPR" else SUF)}], **kw)
            return {"id": p["id"], "m": k, "j": j, "text": "".join(b.text for b in x.content if b.type == "text"), "in": x.usage.input_tokens, "out": x.usage.output_tokens, "error": None}
        except (APIStatusError, APIConnectionError) as e: err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
    return {"id": p["id"], "m": k, "j": j, "text": "", "in": 0, "out": 0, "error": err}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); probs = make_hard(); jobs = [(p, k, j) for p in probs for k, n in PLAN for j in range(n)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(lambda jb: one(cl, jb), jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
