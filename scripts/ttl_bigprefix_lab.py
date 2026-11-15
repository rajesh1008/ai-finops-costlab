#!/usr/bin/env python3
"""Ch18 lab (53rd run). REAL calls. What does a ~30,000-token prefix cost to write with the 5-minute and the 1-hour
cache lifetime, and what do the next three reads (2 s apart) cost? 3 chains per arm, own nonce, max_tokens 8.
Cost from usage fields. Model claude-haiku-4-5-20251001. Key from env only, never printed."""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from cache_race_lab import cost
from cache_bigprefix_lab import big
M = "claude-haiku-4-5-20251001"
OUT = Path(__file__).resolve().parents[1] / "runs" / "ttl-bigprefix-lab-2026-11-15.jsonl"
def one(cl, nonce, k, ttl):
    cc = {"type": "ephemeral"}
    if ttl == "1h": cc["ttl"] = "1h"
    r = cl.messages.create(model=M, max_tokens=8, system=[{"type": "text", "text": big(nonce), "cache_control": cc}],
                           messages=[{"role": "user", "content": f"Ping {k}. Say ok."}])
    us = r.usage
    u = {"k": k, "in": us.input_tokens, "out": us.output_tokens, "cr": us.cache_read_input_tokens or 0, "cw": us.cache_creation_input_tokens or 0}
    cc_ = getattr(us, "cache_creation", None)
    if cc_ is not None:
        u["cw5m_field"] = getattr(cc_, "ephemeral_5m_input_tokens", None); u["cw1h_field"] = getattr(cc_, "ephemeral_1h_input_tokens", None)
    u["cost"] = cost(u, ttl); return u
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); res = []
    for rep in range(3):
        for ttl in ("5m", "1h"):
            nonce = f"ttl{ttl}-{rep}-{int(time.time())}"; rows = []
            for k in range(4):
                try: rows.append(one(cl, nonce, k, ttl))
                except Exception as e: rows.append({"k": k, "error": type(e).__name__ + ": " + str(e)[:160]})
                time.sleep(2)
            res.append({"ttl": ttl, "rep": rep, "rows": rows})
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
def summarise(rows):
    out = {}
    for t in ("5m", "1h"):
        c = [r for r in rows if r["ttl"] == t]; ok = [u for r in c for u in r["rows"] if "error" not in u]
        w = [r["rows"][0] for r in c if "error" not in r["rows"][0]]
        out[t] = {"chains": len(c), "calls": len(ok), "reads": sum(u["cr"] > 0 for u in ok),
                  "write_call_cost": sum(u["cost"] for u in w) / max(1, len(w)),
                  "mean_chain_cost": sum(u["cost"] for u in ok) / max(1, len(c)),
                  "prefix_tokens": max((u["cr"] + u["cw"] for u in ok), default=0)}
    return out
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    for t, s in summarise(rows).items(): print(t, s)
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
