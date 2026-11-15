#!/usr/bin/env python3
"""Chapter 45 lab, REAL calls. 8 task types x 5 variants (40 synthetic Fieldstone prompts), each called 5 times on claude-haiku-4-5-20251001 and claude-haiku-5-5 (thinking disabled),
max_tokens 600, default temperature. 400 calls. Records input and output tokens per call. Output runs/forecast-variance-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
OUT = Path(__file__).resolve().parents[1] / "runs" / "forecast-variance-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
TYPES = {
 "explain": "Explain to a customer in plain language what happens to their {x} when {y}.",
 "reply": "Write a reply to this customer message from Fieldstone Analytics support: \"{y}\"",
 "summarise": "Summarise the following situation for an account manager: {y}",
 "steps": "List the steps a customer should take to {y}.",
 "compare": "Compare two options for a customer who wants to {y}.",
 "classify": "Give the category and a one-line reason for this ticket: {y}",
 "rewrite": "Rewrite this sentence so a non-technical reader understands it: {y}",
 "plan": "Draft a short plan for a customer who needs to {y}.",
}
TOPICS = ["export a quarterly report", "change the owner of a dashboard", "understand an unexpected charge for scheduled reports", "share a workspace with a contractor", "recover a deleted saved query"]
def prompts():
    out = []
    for t, tpl in TYPES.items():
        for k, y in enumerate(TOPICS):
            out.append({"id": f"{t}-{k}", "type": t, "text": tpl.format(x="saved reports", y=y)})
    return out
def call(cl, model, kw, text):
    for att in range(4):
        try:
            r = cl.messages.create(model=model, max_tokens=600, messages=[{"role": "user", "content": text}], **kw)
            return r.usage.input_tokens, r.usage.output_tokens, r.stop_reason
        except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
    return None
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); P = prompts()
    jobs = [(m, p, r) for m in MODELS for p in P for r in range(5)]
    def one(j):
        m, p, r = j; res = call(cl, MODELS[m][0], MODELS[m][1], p["text"])
        return {"m": m, "id": p["id"], "type": p["type"], "rep": r, "tin": res[0] if res else None, "tout": res[1] if res else None, "stop": res[2] if res else "api_error"}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "api_errors", sum(1 for r in res if r["stop"] == "api_error"))
if __name__ == "__main__": main()
