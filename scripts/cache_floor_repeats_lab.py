#!/usr/bin/env python3
"""Chapter 18 lab, repeat and floor search. REAL calls. Each prompt size is sent three times per model (fresh salt each time, so no shared cache). Haiku 4.5 gets the original nine sizes; haiku 5.5 gets those plus smaller sizes (20 to 250 target tokens) to look for its cache floor below 651 tokens. cache_control on the whole system block, max_tokens 5. Reports actual prompt size and whether a cache write happened."""
import os, sys, json, random, time
from pathlib import Path
MODELS = {"claude-haiku-4-5-20251001": [300, 500, 800, 1100, 1500, 2100, 3000, 4200, 5000],
          "claude-haiku-5-5": [20, 50, 100, 200, 300, 500, 800, 1100, 1500, 2100, 3000, 4200, 5000]}
REPEATS = 3
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-floor-repeats-2026-11-12.jsonl"
WORDS = "ledger tenant refund window tier clause notice retention escalate invoice quota credit renewal audit region seat export".split()
def filler(n_words, seed):
    r = random.Random(seed)
    return " ".join(r.choice(WORDS) + (str(r.randint(10, 99)) if r.random() < .3 else "") for _ in range(n_words))
def total(r): return r["input"] + r["write"] + r["read"]
def summarise(rows):
    out = {}
    for m in sorted({r["model"] for r in rows}):
        rs = [r for r in rows if r["model"] == m and "input" in r]
        cached = [total(r) for r in rs if r["write"] > 0]
        unc = [total(r) for r in rs if r["write"] == 0 and r["read"] == 0]
        per = {}
        for r in rs: per.setdefault(r["target"], []).append(r["write"] > 0)
        out[m] = {"smallest_cached": min(cached) if cached else None, "largest_uncached": max(unc) if unc else None,
                  "cells_all_cached": sorted(t for t, v in per.items() if all(v)),
                  "cells_mixed": sorted(t for t, v in per.items() if any(v) and not all(v)),
                  "cells_none_cached": sorted(t for t, v in per.items() if not any(v)), "n": len(rs),
                  "errors": sum(1 for r in rows if r["model"] == m and "error" in r)}
    return out
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); rows = []
    for m, targets in MODELS.items():
        for rep in range(REPEATS):
            for k, t in enumerate(targets):
                text = f"Salt {m} {t} {rep} {time.time()}.\n" + filler(max(1, int(t * 0.75)), k * 10 + rep)
                try:
                    x = cl.messages.create(model=m, max_tokens=5, system=[{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}],
                                           messages=[{"role": "user", "content": "Reply with the single word OK."}])
                    u = x.usage
                    rows.append({"model": m, "target": t, "rep": rep, "input": u.input_tokens, "write": u.cache_creation_input_tokens or 0, "read": u.cache_read_input_tokens or 0})
                except Exception as e:
                    rows.append({"model": m, "target": t, "rep": rep, "error": type(e).__name__ + ": " + str(e)[:200]})
                time.sleep(0.4)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        rows = [json.loads(l) for l in OUT.read_text().splitlines()]
        for r in rows:
            print(r["model"], r["target"], r["rep"], ("ERROR " + r["error"]) if "error" in r else f'total {total(r)} write {r["write"]} read {r["read"]}')
        print(json.dumps(summarise(rows), indent=1))
    else: main()
