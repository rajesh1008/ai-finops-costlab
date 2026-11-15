#!/usr/bin/env python3
"""Chapter 48 follow-up lab (eighteenth run), REAL calls. Locates the cache minimum by sweeping prefix size.
claude-haiku-4-5: 8 sizes between about 3,900 and 5,100 tokens. claude-haiku-5-5 (thinking disabled): 9 sizes between about 100 and 1,800 tokens.
Each size is called twice with cache_control on the system block; a unique salt per run keeps earlier runs from being read. Output runs/canary-edge-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time, uuid
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
OUT = Path(__file__).resolve().parents[1] / "runs" / "canary-edge-lab-2026-11-11.json"
BASE = "Fieldstone Analytics support note: the customer asks how scheduled reports are billed, whether exports count against the plan, and who can change the owner of a dashboard. "
SWEEP = {"h45": ("claude-haiku-4-5-20251001", {}, [3990, 4040, 4080, 4096, 4110, 4150, 4300, 4600]),
         "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}}, [150, 300, 500, 700, 900, 1100, 1300, 1500, 1700])}
def retry(f):
    for a in range(4):
        try: return f()
        except (APIStatusError, APIConnectionError): time.sleep(2 * (a + 1))
    raise RuntimeError("api failure")
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); rows = []; salt = uuid.uuid4().hex[:8]
    for m, (model, kw, targets) in SWEEP.items():
        for tgt in targets:
            reps = 1
            def build(r): return f"[{salt}-{tgt}] " + BASE * r
            msgs = [{"role": "user", "content": "Answer in one word: is this a billing question?"}]
            def n_of(r): return retry(lambda: cl.messages.count_tokens(model=model, system=[{"type": "text", "text": build(r), "cache_control": {"type": "ephemeral"}}], messages=msgs)).input_tokens
            n = n_of(reps)
            per = max(1, n_of(2) - n)
            # grow the prefix by repeating BASE until the counted size is at or just above the target, then trim by words to land close
            reps = max(1, (tgt - n) // per + 1)
            text = build(reps)
            words = text.split(" ")
            sysb = lambda w: [{"type": "text", "text": " ".join(words[:w]), "cache_control": {"type": "ephemeral"}}]
            lo, hi = 1, len(words)
            while lo < hi:   # largest word count whose counted size is <= tgt
                mid = (lo + hi + 1) // 2
                c = retry(lambda: cl.messages.count_tokens(model=model, system=sysb(mid), messages=msgs)).input_tokens
                if c <= tgt: lo = mid
                else: hi = mid - 1
            s = sysb(lo)
            c = retry(lambda: cl.messages.count_tokens(model=model, system=s, messages=msgs)).input_tokens
            r1 = retry(lambda: cl.messages.create(model=model, max_tokens=5, system=s, messages=msgs, **kw)).usage
            time.sleep(1)
            r2 = retry(lambda: cl.messages.create(model=model, max_tokens=5, system=s, messages=msgs, **kw)).usage
            rows.append({"m": m, "target": tgt, "counted": c, "write_first": r1.cache_creation_input_tokens or 0, "read_second": r2.cache_read_input_tokens or 0})
            print(m, tgt, c, rows[-1]["write_first"], rows[-1]["read_second"], flush=True)
    OUT.write_text(json.dumps({"results": rows})); print("saved", OUT.name, len(rows))
if __name__ == "__main__": main()
