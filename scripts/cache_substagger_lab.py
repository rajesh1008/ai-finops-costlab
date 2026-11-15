#!/usr/bin/env python3
"""Ch18 / Ch25 lab (51st run, sub-second gaps). REAL calls. How far apart must calls start before the second one reads the cache?
Four calls share a ~4,700-token cached prefix and start gap seconds apart (gap 0,0.1,0.2,0.4,0.8; 4 repeats each, own nonce).
Cost from the usage fields. Model claude-haiku-4-5-20251001. Key from env only, never printed."""
import os, sys, json, time, random, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from cache_race_lab import doc, cost
M = "claude-haiku-4-5-20251001"
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-substagger-lab-2026-11-15.jsonl"
GAPS = [0, 0.1, 0.2, 0.4, 0.8]; N = 4
def one(cl, nonce, k, rows, t0):
    try:
        s = time.time() - t0
        r = cl.messages.create(model=M, max_tokens=8, system=[{"type": "text", "text": doc(nonce), "cache_control": {"type": "ephemeral"}}],
                               messages=[{"role": "user", "content": f"Ping {k}. Say ok."}])
        us = r.usage
        u = {"k": k, "start_s": round(s, 2), "end_s": round(time.time() - t0, 2), "in": us.input_tokens, "out": us.output_tokens,
             "cr": us.cache_read_input_tokens or 0, "cw": us.cache_creation_input_tokens or 0}
        u["cost"] = cost(u); rows.append(u)
    except Exception as e:
        rows.append({"k": k, "error": type(e).__name__ + ": " + str(e)[:160]})
def chain(cl, gap, rep, res):
    nonce = f"substagger{gap}-{rep}-{random.Random(f'{gap}-{rep}').randint(10**6, 10**7)}"; rows = []; th = []; t0 = time.time()
    for k in range(N):
        t = threading.Thread(target=one, args=(cl, nonce, k, rows, t0)); t.start(); th.append(t)
        if k < N - 1: time.sleep(gap)
    for t in th: t.join()
    res.append({"gap": gap, "rep": rep, "rows": sorted(rows, key=lambda u: u["k"])})
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); res = []
    for rep in range(4):
        for g in GAPS: chain(cl, g, rep, res)
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
def summarise(rows):
    out = {}
    for g in GAPS:
        c = [r for r in rows if r["gap"] == g]
        allc = [u for r in c for u in r["rows"] if "error" not in u]
        if not allc: continue
        out[g] = {"chains": len(c), "calls": len(allc), "reads": sum(u["cr"] > 0 for u in allc), "writes": sum(u["cw"] > 0 for u in allc),
                  "mean_cost_per_chain": sum(u["cost"] for u in allc) / len(c),
                  "mean_latency_s": sum(u["end_s"] - u["start_s"] for u in allc) / len(allc)}
    return out
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    for g, s in summarise(rows).items(): print("gap", g, s)
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
