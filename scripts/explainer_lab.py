#!/usr/bin/env python3
"""Chapter 38 lab, REAL calls. An agent is shown a week-over-week table for one product and asked to name the one driver of the change.
Scenarios: 6 drivers x 4 products x K=2 seeds = 48, each shown two ways: T (spend and calls only) and D (calls, tokens per call, dear-model share, cache read share, price index, untagged share).
Models: claude-haiku-4-5-20251001 and claude-haiku-5-5 (thinking disabled, max_tokens 300). The true driver is known by construction. Output runs/explainer-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.explainer import *
OUT = Path(__file__).resolve().parents[1] / "runs" / "explainer-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
SYS = "You are a cost analyst. You see a week-over-week table for one AI product and must name the single most likely driver of the spend change."
ASK = ('Choose one driver from: volume, price, cache, tokens_per_call, mix, untagged, unknown. "volume" means more calls; "price" means the rate card changed; "cache" means a lower share of input read from cache; '
       '"tokens_per_call" means longer prompts per call; "mix" means more calls to the dearer model; "untagged" means spend moved out of the tagged set; "unknown" means the table cannot tell. '
       'Reply with JSON only: {"driver": "...", "evidence": "one sentence"}.')
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = []
    for p in ["support-agent", "extraction", "reports", "search"]:
        for d in DRIVERS:
            for k in range(2):
                a, b = scenario(p, d, 380 + k * 17 + hash((p, d)) % 1 )
                for form in ("T", "D"):
                    for m in MODELS: jobs.append((p, d, k, form, m, table(p, a, b, form == "D")))
    def one(j):
        p, d, k, form, m, tb = j; model, kw = MODELS[m]
        for att in range(4):
            try:
                r = cl.messages.create(model=model, max_tokens=300, system=SYS, messages=[{"role": "user", "content": tb + "\n\n" + ASK}], **kw)
                return {"p": p, "true": d, "k": k, "form": form, "m": m, "in": r.usage.input_tokens, "out": r.usage.output_tokens, "text": "".join(x.text for x in r.content if x.type == "text"), "error": None}
            except Exception as e:
                time.sleep(2 * (att + 1)); err = type(e).__name__
        return {"p": p, "true": d, "k": k, "form": form, "m": m, "in": 0, "out": 0, "text": "", "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
