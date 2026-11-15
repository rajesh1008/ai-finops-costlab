#!/usr/bin/env python3
"""Ch22 / Ch18 lab (52nd run). REAL calls. Why were 5 of 48 replies in the long-reply lab only 5 to 7 tokens?
Same user prompt, 50 calls per arm, reply TEXT stored. Arm A: the long-reply lab's cached system document (it contains the line
'You are a terse assistant. Reply with one short word.'). Arm B: the same document with that line replaced by a neutral line.
Model claude-haiku-4-5-20251001, max_tokens 450. Key from env only, never printed."""
import os, sys, json, time, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from cache_race_lab import doc, cost
M = "claude-haiku-4-5-20251001"
OUT = Path(__file__).resolve().parents[1] / "runs" / "short-reply-lab-2026-11-15.jsonl"
PROMPT = "Ping 0. Write a 300-word note on why invoices and meters disagree."
ARMS = {"A_terse_line": lambda n: doc(n),
        "B_neutral_line": lambda n: doc(n).replace("You are a terse assistant. Reply with one short word.", "You are a careful assistant for a finance team.")}
N = 50
def one(cl, arm, i):
    nonce = f"shortreply-{arm[0]}-{i % 5}"
    try:
        r = cl.messages.create(model=M, max_tokens=450, system=[{"type": "text", "text": ARMS[arm](nonce), "cache_control": {"type": "ephemeral"}}],
                               messages=[{"role": "user", "content": PROMPT}])
        us = r.usage
        u = {"arm": arm, "i": i, "in": us.input_tokens, "out": us.output_tokens, "cr": us.cache_read_input_tokens or 0,
             "cw": us.cache_creation_input_tokens or 0, "stop": r.stop_reason, "text": r.content[0].text if r.content else ""}
        u["cost"] = cost(u); return u
    except Exception as e:
        return {"arm": arm, "i": i, "error": type(e).__name__ + ": " + str(e)[:160]}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    for arm in ARMS:  # prime each of the 5 documents once, then the rest in parallel
        rows += [one(cl, arm, i) for i in range(5)]
        with ThreadPoolExecutor(5) as ex: rows += list(ex.map(lambda i: one(cl, arm, i), range(5, N)))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summarise(rows, short=60):
    out = {}
    for arm in ARMS:
        r = [x for x in rows if x["arm"] == arm and "error" not in x]
        if not r: continue
        outs = sorted(x["out"] for x in r)
        out[arm] = {"calls": len(r), "short": sum(x["out"] < short for x in r), "median_out": outs[len(outs) // 2],
                    "min_out": outs[0], "max_out": outs[-1], "max_tokens_stops": sum(x["stop"] == "max_tokens" for x in r),
                    "cost": sum(x["cost"] for x in r)}
    return out
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    for a, s in summarise(rows).items(): print(a, s)
    for x in rows:
        if "error" not in x and x["out"] < 60: print("SHORT", x["arm"], x["i"], x["out"], repr(x["text"][:200]))
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
