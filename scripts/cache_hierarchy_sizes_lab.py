#!/usr/bin/env python3
"""Chapter 18 lab (follow-up). REAL calls. Tests the guess that haiku-4-5 rewrote everything on a system edit because the tool block sat under the 4,096-token minimum. Tool block at three sizes (600, 2,400 and 4,800 words of filler; the billed tool block came to about 1,300, 4,600 and 8,900 tokens on haiku-4-5, derived from the totals), system block fixed (3,213 tokens on haiku-4-5, 4,928 on haiku-5-5). Per model, size and repeat (fresh salt): warm, then system-changed. Reports input, cache write, cache read."""
import os, sys, json, random, time
from pathlib import Path
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
SIZES = {"small": 600, "medium": 2400, "large": 4800}
REPEATS = 3
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-hierarchy-sizes-2026-11-12.jsonl"
WORDS = "ledger tenant refund window tier clause notice retention escalate invoice quota credit renewal audit region seat export".split()
def filler(n, seed):
    r = random.Random(seed); return " ".join(r.choice(WORDS) + (str(r.randint(10, 99)) if r.random() < .3 else "") for _ in range(n))
def build(salt, tool_words, sys_variant=0):
    tools = [{"name": "lookup_account", "description": f"Look up an account. {salt} " + filler(tool_words, 1),
              "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
              "cache_control": {"type": "ephemeral"}}]
    system = [{"type": "text", "text": f"Handbook {salt}. " + filler(1800, 3) + (" Changed rule." if sys_variant else ""), "cache_control": {"type": "ephemeral"}}]
    return dict(tools=tools, system=system, messages=[{"role": "user", "content": "Reply with the single word OK."}], max_tokens=5, tool_choice={"type": "none"})
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    def call(m, size, rep, label, **kw):
        u = cl.messages.create(model=m, **build(**kw)).usage
        rows.append({"model": m, "size": size, "rep": rep, "cell": label, "input": u.input_tokens, "write": u.cache_creation_input_tokens or 0, "read": u.cache_read_input_tokens or 0}); time.sleep(0.4)
    for m in MODELS:
        for size, w in SIZES.items():
            for rep in range(REPEATS):
                salt = f"{m}-{size}-{rep}-{time.time()}"
                call(m, size, rep, "warm", salt=salt, tool_words=w)
                call(m, size, rep, "system_changed", salt=salt, tool_words=w, sys_variant=1)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]
    for r in rows: print(r["model"], r["size"], r["rep"], r["cell"], "input", r["input"], "write", r["write"], "read", r["read"])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
