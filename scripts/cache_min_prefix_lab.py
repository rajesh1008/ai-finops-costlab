#!/usr/bin/env python3
"""Chapter 18 lab. REAL calls. Does a prefix below the documented minimum cacheable length really get processed without caching and without an error? One call per prefix size per model, cache_control on the whole system block, max_tokens 5. The filler is synthetic clause text, salted so no two calls share a cache. Reports the actual prompt size (input + cache write + cache read) and whether a cache write happened."""
import os, sys, json, random, time
from pathlib import Path
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
TARGETS = [300, 500, 800, 1100, 1500, 2100, 3000, 4200, 5000]
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-min-prefix-2026-11-12.jsonl"
WORDS = "ledger tenant refund window tier clause notice retention escalate invoice quota credit renewal audit region seat export".split()
def filler(n_words, seed):
    r = random.Random(seed)
    return " ".join(r.choice(WORDS) + (str(r.randint(10, 99)) if r.random() < .3 else "") for _ in range(n_words))
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    for m in MODELS:
        for k, t in enumerate(TARGETS):
            text = f"Salt {m} {t} 2026-11-12 {time.time()}.\n" + filler(int(t * 0.75), k)
            x = cl.messages.create(model=m, max_tokens=5, system=[{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}],
                                   messages=[{"role": "user", "content": "Reply with the single word OK."}])
            u = x.usage
            rows.append({"model": m, "target": t, "input": u.input_tokens, "write": u.cache_creation_input_tokens or 0, "read": u.cache_read_input_tokens or 0})
            time.sleep(0.5)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
def summarise(rows):
    out = {}
    for m in {r["model"] for r in rows}:
        rs = sorted((r for r in rows if r["model"] == m), key=lambda r: r["input"] + r["write"] + r["read"])
        total = lambda r: r["input"] + r["write"] + r["read"]
        cached = [total(r) for r in rs if r["write"] > 0]
        uncached = [total(r) for r in rs if r["write"] == 0 and r["read"] == 0]
        out[m] = {"smallest_cached": min(cached) if cached else None, "largest_uncached": max(uncached) if uncached else None}
    return out
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        rows = [json.loads(l) for l in OUT.read_text().splitlines()]
        for r in rows: print(r["model"], r["target"], "total", r["input"] + r["write"] + r["read"], "write", r["write"], "read", r["read"])
        print(json.dumps(summarise(rows), indent=1))
    else: main()
