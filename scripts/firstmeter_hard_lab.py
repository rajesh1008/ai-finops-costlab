#!/usr/bin/env python3
"""Chapter 42 follow-up lab (nineteenth run), REAL calls. 120 SYNTHETIC requests (4 overlapping features x 30). View U: user message only. View G: a generic system prompt shared by all
features plus the user message. Two models (claude-haiku-4-5-20251001, claude-haiku-5-5 thinking disabled), unknown allowed. 120 x 2 x 2 = 480 calls. Output runs/firstmeter-hard-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.firstmeter_hard import make_hard, HARD, GENERIC
OUT = Path(__file__).resolve().parents[1] / "runs" / "firstmeter-hard-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
CAT = ("sql_helper: writes read-only SQL from questions\nreport_summariser: summarises weekly analytics reports for executives\n"
       "metric_explainer: explains what a dashboard metric means or why it moved, for internal analysts\nsupport_assistant: answers customer support questions using the handbook")
def prompt(r, view):
    body = (f"System prompt of the call: \"{GENERIC}\"\n" if view == "G" else "") + f"User message of the call: \"{r['user']}\"\n"
    return ("A company logged an LLM call with no cost tag. Features:\n" + CAT + "\n\n" + body +
            'Which feature made the call? If you cannot tell, say unknown. Reply with JSON only: {"feature": "<one of the four names or unknown>"}.')
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); reqs = make_hard(); jobs = [(i, r, m, v) for i, r in enumerate(reqs) for m in MODELS for v in "UG"]
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
