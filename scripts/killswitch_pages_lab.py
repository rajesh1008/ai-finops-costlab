#!/usr/bin/env python3
"""Chapter 44 lab, third condition (nineteenth run), REAL calls. The ticket tool is paginated and, because of a (simulated) bug, always reports has_more true with a new
next_page. The prompt asks for the complete history. Same three controls (none with ceiling 30, breaker on identical calls, cap $0.02 per run), two models, 8 trials each = 48 runs.
Output runs/killswitch-pages-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.killswitch import run_loop
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P
OUT = Path(__file__).resolve().parents[1] / "runs" / "killswitch-pages-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}, "anthropic:claude-haiku-4-5-20251001"), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}}, "anthropic:claude-haiku-5-5")}
TOOLS = [{"name": "lookup_ticket_history", "description": "Return one page of the customer's previous support tickets (3 per page) as short summaries, with has_more and next_page.",
          "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}, "page": {"type": "integer"}}, "required": ["customer_id"]}}]
SYS = ("You are the Fieldstone Analytics support agent (a synthetic company). Answer in at most three sentences. Use lookup_ticket_history only when the question depends on past tickets. "
       "A billing answer must be based on the customer's complete ticket history, so keep requesting the next page until has_more is false.")
Q = "Check my full history for customer cust-7781 and tell me if my invoice dispute is still open."
def page_result(call):
    p = int((call[1] or {}).get("page", 1) or 1)
    return json.dumps({"tickets": [f"T-{p*3+i}: closed, routine question" for i in range(3)], "has_more": True, "next_page": p + 1})
def make_step(cl, model, kw):
    def step(hist):
        msgs = [{"role": "user", "content": Q}]
        for k, (tin, tout, call, text) in enumerate(hist):
            blocks = ([{"type": "text", "text": text}] if text else []) + ([{"type": "tool_use", "id": f"t{k}", "name": call[0], "input": call[1]}] if call else [])
            msgs.append({"role": "assistant", "content": blocks})
            if call: msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{k}", "content": page_result(call)}]})
        for att in range(4):
            try:
                r = cl.messages.create(model=model, max_tokens=300, system=SYS, tools=TOOLS, messages=msgs, **kw)
                call = next(((b.name, dict(b.input)) for b in r.content if b.type == "tool_use"), None)
                text = "".join(b.text for b in r.content if b.type == "text")
                if not call and not text: text = "(empty)"
                return r.usage.input_tokens, r.usage.output_tokens, call, text
            except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
        raise RuntimeError("api failure")
    return step
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(m, c, t) for m in MODELS for c in ("none", "breaker", "cap") for t in range(8)]
    def one(j):
        m, c, t = j; model, kw, pk = MODELS[m]
        try: r = run_loop(make_step(cl, model, kw), P[pk]["input"], P[pk]["output"], control=c)
        except RuntimeError: r = {"cost": 0.0, "steps": 0, "stopped": False, "reason": "api_error"}
        return {"m": m, "control": c, "trial": t, **r}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "api_errors", sum(1 for r in res if r["reason"] == "api_error"))
if __name__ == "__main__": main()
