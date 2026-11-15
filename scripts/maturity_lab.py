#!/usr/bin/env python3
"""Chapter 41 lab, REAL calls. 48 SYNTHETIC evidence statements (8 capabilities x 6, author-assigned levels, three of the six per capability are decoys) are judged by two models under two prompts:
F (free): 'which level is this: crawl, walk or run?'  G (gated): the same plus the rubric's artefact for each level and the rule that adjectives, plans and claims without the named artefact do not count.
Models: claude-haiku-4-5-20251001 and claude-haiku-5-5 (thinking disabled), max_tokens 200. 48 x 2 x 2 = 192 calls. Output runs/maturity-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.maturity import STATEMENTS, ARTEFACT, LEVELS
OUT = Path(__file__).resolve().parents[1] / "runs" / "maturity-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
SYS = "You assess how mature a company's AI cost management practice is, one capability at a time, using the FinOps vocabulary crawl, walk, run."
def prompt(s, mode):
    base = f"Capability: {s['cap'].replace('_', ' ')}.\nStatement from the company: \"{s['text']}\"\n\n"
    if mode == "G":
        a = ARTEFACT[s["cap"]]
        base += (f"Rubric. Walk requires this artefact: {a[1]}. Run requires this artefact AND the walk artefact: {a[2]}. Crawl is everything else. "
                 "Adjectives, plans, intentions and claims that do not describe the artefact do not count. Choose the highest level the statement actually supports.\n")
    return base + 'Reply with JSON only: {"level": "crawl" or "walk" or "run", "reason": "one sentence"}.'
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(i, s, m, mode) for i, s in enumerate(STATEMENTS) for m in MODELS for mode in "FG"]
    def one(j):
        i, s, m, mode = j; model, kw = MODELS[m]; err = None
        for att in range(4):
            try:
                r = cl.messages.create(model=model, max_tokens=200, system=SYS, messages=[{"role": "user", "content": prompt(s, mode)}], **kw)
                return {"i": i, "m": m, "mode": mode, "in": r.usage.input_tokens, "out": r.usage.output_tokens, "text": "".join(b.text for b in r.content if b.type == "text"), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
        return {"i": i, "m": m, "mode": mode, "in": 0, "out": 0, "text": "", "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
