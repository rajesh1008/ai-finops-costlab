#!/usr/bin/env python3
"""Chapter 18 lab (second follow-up). REAL calls. Locates the caching floor on haiku-4-5 between the 1,300 and 4,600 token tool blocks of the previous lab: tool block of 1,200, 1,750, 2,050, 2,150 and 2,300 words of filler (about 2,500 to 4,600 tokens, derived from totals), system block fixed. Per size and repeat (fresh salt): warm, then system-changed. Reports input, write, read."""
import os, sys, json, random, time
from pathlib import Path
MODELS = ["claude-haiku-4-5-20251001"]
SIZES = {"w1200": 1200, "w1750": 1750, "w2050": 2050, "w2150": 2150, "w2300": 2300}
REPEATS = 3
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-hierarchy-gap-2026-11-13.jsonl"
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
