#!/usr/bin/env python3
"""Chapter 42 lab, REAL calls. 160 SYNTHETIC untagged requests (4 features x 40). Each model is asked which feature produced the request, under
two views: S (system prompt and user message) and U (user message only), each with an 'unknown' option. Models: claude-haiku-4-5-20251001 and claude-haiku-5-5 (thinking disabled).
160 x 2 x 2 = 640 calls, max_tokens 150. Output runs/firstmeter-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.firstmeter import make_requests, NAMES
OUT = Path(__file__).resolve().parents[1] / "runs" / "firstmeter-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
CAT = ("support_assistant: answers customer support questions from the handbook\nreport_summariser: summarises weekly analytics reports\n"
       "sql_helper: writes read-only SQL from questions\nonboarding_emailer: drafts onboarding emails to new workspace owners")
def prompt(r, view):
    body = (f"System prompt of the call: \"{r['system']}\"\n" if view == "S" else "") + f"User message of the call: \"{r['user']}\"\n"
    return ("A company logged an LLM call with no cost tag. Features:\n" + CAT + "\n\n" + body +
            'Which feature made the call? If you cannot tell, say unknown. Reply with JSON only: {"feature": "<one of the four names or unknown>"}.')
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); reqs = make_requests(); jobs = [(i, r, m, v) for i, r in enumerate(reqs) for m in MODELS for v in "SU"]
    def one(j):
        i, r, m, v = j; model, kw = MODELS[m]; err = None
        for att in range(4):
            try:
                x = cl.messages.create(model=model, max_tokens=150, messages=[{"role": "user", "content": prompt(r, v)}], **kw)
                return {"i": i, "m": m, "view": v, "in": x.usage.input_tokens, "out": x.usage.output_tokens, "text": "".join(b.text for b in x.content if b.type == "text"), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
        return {"i": i, "m": m, "view": v, "in": 0, "out": 0, "text": "", "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"requests": reqs, "results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
