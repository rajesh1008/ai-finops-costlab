#!/usr/bin/env python3
"""Chapter 18 lab. REAL calls. The cache prefix order is tools, then system, then messages. Which edits break which read? Per model: warm (tools T1 + system S1, breakpoints on the last tool and the system block), then (a) same again, (b) system changed only, (c) one tool description changed, (d) user turn changed only, each preceded by a re-warm of the base so the cells are independent. Tool and system text are synthetic, salted per run, about 2,500 words each part. Reports input, cache write, cache read tokens per call."""
import os, sys, json, random, time
from pathlib import Path
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-hierarchy-2026-11-12.jsonl"
WORDS = "ledger tenant refund window tier clause notice retention escalate invoice quota credit renewal audit region seat export".split()
def filler(n, seed):
    r = random.Random(seed); return " ".join(r.choice(WORDS) + (str(r.randint(10, 99)) if r.random() < .3 else "") for _ in range(n))
def build(salt, tool_variant=0, sys_variant=0, user="Reply with the single word OK."):
    tools = [{"name": "lookup_account", "description": f"Look up an account. {salt} " + filler(1800, 1) + (" Revised wording." if tool_variant else ""),
              "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
             {"name": "issue_credit", "description": "Issue a credit. " + filler(300, 2),
              "input_schema": {"type": "object", "properties": {"amount": {"type": "number"}}, "required": ["amount"]},
              "cache_control": {"type": "ephemeral"}}]
    system = [{"type": "text", "text": f"Handbook {salt}. " + filler(1800, 3) + (" Changed rule." if sys_variant else ""), "cache_control": {"type": "ephemeral"}}]
    return dict(tools=tools, system=system, messages=[{"role": "user", "content": user}], max_tokens=5, tool_choice={"type": "none"})
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    def call(m, label, **kw):
        u = cl.messages.create(model=m, **build(**kw)).usage
        rows.append({"model": m, "cell": label, "input": u.input_tokens, "write": u.cache_creation_input_tokens or 0, "read": u.cache_read_input_tokens or 0}); time.sleep(0.5)
    for m in MODELS:
        salt = f"{m}-{time.time()}"
        call(m, "warm", salt=salt)
        call(m, "same", salt=salt)
        call(m, "user_changed", salt=salt, user="Reply with the single word DONE.")
        call(m, "system_changed", salt=salt, sys_variant=1)
        call(m, "tool_changed", salt=salt, tool_variant=1)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        for l in OUT.read_text().splitlines():
            r = json.loads(l); print(r["model"], r["cell"], "input", r["input"], "write", r["write"], "read", r["read"])
    else: main()
