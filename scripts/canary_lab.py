#!/usr/bin/env python3
"""Chapter 48 lab, REAL calls. Canary battery on claude-haiku-4-5-20251001 and claude-haiku-5-5 (thinking disabled):
 1. count_tokens equals usage.input_tokens on 10 prompts of rising length (max_tokens 5).  2. count_tokens twice gives the same number.
 3. cache: a prefix of about 3,000 and about 5,000 tokens with cache_control; the second identical call must read the cache only at or above the documented minimum (4,096 for haiku-4-5; haiku-5-5 minimum is read from the observation, not assumed).
Output runs/canary-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.canary import count_matches_usage, counts_deterministic, cache_expected
OUT = Path(__file__).resolve().parents[1] / "runs" / "canary-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}, 4096), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}}, None)}
BASE = "Fieldstone Analytics support note: the customer asks how scheduled reports are billed, whether exports count against the plan, and who can change the owner of a dashboard. "
def retry(f):
    for att in range(4):
        try: return f()
        except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
    raise RuntimeError("api failure")
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); rows = []
    for m, (model, kw, minimum) in MODELS.items():
        for k, reps in enumerate([1, 3, 6, 12, 25, 50, 100, 200, 400, 800]):
            text = BASE * reps; msgs = [{"role": "user", "content": text}]
            c1 = retry(lambda: cl.messages.count_tokens(model=model, messages=msgs)).input_tokens
            c2 = retry(lambda: cl.messages.count_tokens(model=model, messages=msgs)).input_tokens
            u = retry(lambda: cl.messages.create(model=model, max_tokens=5, messages=msgs, **kw)).usage.input_tokens
            rows.append({"m": m, "check": "count_vs_usage", "n": c1, "usage": u, "ok": count_matches_usage(c1, u)})
            rows.append({"m": m, "check": "count_deterministic", "n": c1, "ok": counts_deterministic(c1, c2)})
        for reps in (30, 40, 50, 60, 70, 80, 100, 130):   # prefix sizes chosen to straddle 4,096 and the unknown haiku-5-5 minimum
            text = (BASE + "Case ref %d. " % reps) * reps
            sysb = [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
            msgs = [{"role": "user", "content": "Answer in one word: is this a billing question?"}]
            n = retry(lambda: cl.messages.count_tokens(model=model, system=sysb, messages=msgs)).input_tokens
            r1 = retry(lambda: cl.messages.create(model=model, max_tokens=5, system=sysb, messages=msgs, **kw)).usage
            time.sleep(1)
            r2 = retry(lambda: cl.messages.create(model=model, max_tokens=5, system=sysb, messages=msgs, **kw)).usage
            cr = r2.cache_read_input_tokens or 0; cw = r1.cache_creation_input_tokens or 0
            rows.append({"m": m, "check": "cache_read", "prefix_tokens": n, "write_first": cw, "read_second": cr, "ok": (cache_expected(n, minimum, cr) if minimum else None)})
    OUT.write_text(json.dumps({"results": rows})); print("saved", OUT.name, len(rows))
if __name__ == "__main__": main()
