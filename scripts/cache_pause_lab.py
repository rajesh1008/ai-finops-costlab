#!/usr/bin/env python3
"""Ch18 lab (48th run). REAL calls. Cache expiry against user pauses. A ~5k-token system document is cached with a five-minute breakpoint,
then the same prefix is called again after a pause of 30, 240, 330 or 600 seconds (3 repeats each, run in parallel threads, own nonce each).
A fifth arm keeps the cache warm: pings at 240 and 480 seconds, then the real call at 600. Cost from the usage fields the API returned.
Model claude-haiku-4-5-20251001. Key from env only, never printed."""
import os, sys, json, time, random, threading
from pathlib import Path
M = "claude-haiku-4-5-20251001"; P = dict(inp=1.00, out=5.00, cr=0.10, cw=1.25)
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-pause-lab-2026-11-15.jsonl"
WORDS = "ledger invoice meter quota budget tenant gateway tag token batch cache prefix route retry ticket owner forecast variance alert policy region rate window credit refund account review tier limit usage report".split()
def doc(nonce):
    rng = random.Random(nonce)
    return f"Session {nonce}. You are a terse assistant. Reply with one short word.\n\n" + "\n".join(
        f"Section {i}. " + " ".join(rng.choice(WORDS) for _ in range(120)) + "." for i in range(1, 36))
def cost(u): return (u["in"] * P["inp"] + u["out"] * P["out"] + u["cr"] * P["cr"] + u["cw"] * P["cw"]) / 1e6
def call(cl, nonce, t):
    r = cl.messages.create(model=M, max_tokens=8, system=[{"type": "text", "text": doc(nonce), "cache_control": {"type": "ephemeral"}}],
                           messages=[{"role": "user", "content": f"Ping {t}. Say ok."}])
    us = r.usage
    u = {"in": us.input_tokens, "out": us.output_tokens, "cr": us.cache_read_input_tokens or 0, "cw": us.cache_creation_input_tokens or 0}
    u["cost"] = cost(u); return u
def chain(cl, arm, rep, schedule, res):
    nonce = f"{arm}-{rep}-{random.Random(arm + str(rep)).randint(10**6, 10**7)}"
    rows, t0 = [], time.time()
    try:
        for k, at in enumerate(schedule):
            wait = at - (time.time() - t0)
            if wait > 0: time.sleep(wait)
            u = call(cl, nonce, k); u["at_s"] = round(time.time() - t0, 1); rows.append(u)
        res.append({"arm": arm, "rep": rep, "rows": rows})
    except Exception as e:
        res.append({"arm": arm, "rep": rep, "rows": rows, "error": type(e).__name__ + ": " + str(e)[:160]})
ARMS = {"gap30": [0, 30], "gap240": [0, 240], "gap330": [0, 330], "gap600": [0, 600], "keepwarm600": [0, 240, 480, 600]}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); res = []; th = []
    for arm, sch in ARMS.items():
        for rep in range(3):
            x = threading.Thread(target=chain, args=(cl, arm, rep, sch, res)); x.start(); th.append(x)
    for x in th: x.join()
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
def summarise(rows):
    out = {}
    for arm in ARMS:
        g = [r for r in rows if r["arm"] == arm and "error" not in r]
        if not g: continue
        last = [r["rows"][-1] for r in g]
        hits = sum(1 for u in last if u["cr"] > 0)
        out[arm] = {"n": len(g), "final_call_hits": hits, "mean_total_cost": sum(sum(u["cost"] for u in r["rows"]) for r in g) / len(g),
                    "mean_final_cost": sum(u["cost"] for u in last) / len(last)}
    return out
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    print("chains", len(rows), "errors", sum("error" in r for r in rows))
    for a, s in summarise(rows).items():
        print(a, "n", s["n"], "final-call cache hits", s["final_call_hits"], "of", s["n"], "mean final call $%.5f" % s["mean_final_cost"], "mean total $%.5f" % s["mean_total_cost"])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
