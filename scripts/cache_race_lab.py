#!/usr/bin/env python3
"""Ch18 / Ch25 lab (49th run). REAL calls. Does a prefix cache help calls that start at the same moment?
Arm burst8: eight calls with the same ~4,700-token cached prefix fired at once (3 repeats, own nonce each).
Arm primed8: one call first, wait for it to finish, then seven fired at once (3 repeats).
Arm ttl1h_600: a one-hour write, second call after 600 seconds (3 repeats); the five-minute version missed at 600 s in the 48th-run lab.
Cost from the usage fields the API returned. Model claude-haiku-4-5-20251001. Key from env only, never printed."""
import os, sys, json, time, random, threading
from pathlib import Path
M = "claude-haiku-4-5-20251001"; P = dict(inp=1.00, out=5.00, cr=0.10, cw5=1.25, cw1h=2.00)
OUT = Path(__file__).resolve().parents[1] / "runs" / "cache-race-lab-2026-11-15.jsonl"
WORDS = "ledger invoice meter quota budget tenant gateway tag token batch cache prefix route retry ticket owner forecast variance alert policy region rate window credit refund account review tier limit usage report".split()
def doc(nonce):
    rng = random.Random(nonce)
    return f"Session {nonce}. You are a terse assistant. Reply with one short word.\n\n" + "\n".join(
        f"Section {i}. " + " ".join(rng.choice(WORDS) for _ in range(120)) + "." for i in range(1, 36))
def cost(u, ttl="5m"):
    w = P["cw1h"] if ttl == "1h" else P["cw5"]
    return (u["in"] * P["inp"] + u["out"] * P["out"] + u["cr"] * P["cr"] + u["cw"] * w) / 1e6
def call(cl, nonce, k, ttl="5m"):
    cc = {"type": "ephemeral"}
    if ttl == "1h": cc["ttl"] = "1h"
    r = cl.messages.create(model=M, max_tokens=8, system=[{"type": "text", "text": doc(nonce), "cache_control": cc}],
                           messages=[{"role": "user", "content": f"Ping {k}. Say ok."}])
    us = r.usage
    u = {"k": k, "in": us.input_tokens, "out": us.output_tokens, "cr": us.cache_read_input_tokens or 0, "cw": us.cache_creation_input_tokens or 0}
    u["cost"] = cost(u, ttl); return u
def burst(cl, nonce, ks, ttl, rows):
    def one(k):
        try: rows.append(call(cl, nonce, k, ttl))
        except Exception as e: rows.append({"k": k, "error": type(e).__name__ + ": " + str(e)[:160]})
    th = [threading.Thread(target=one, args=(k,)) for k in ks]
    for t in th: t.start()
    for t in th: t.join()
def run_chain(cl, arm, rep, res):
    nonce = f"{arm}-{rep}-{random.Random(arm + str(rep)).randint(10**6, 10**7)}"; rows = []
    try:
        if arm == "burst8": burst(cl, nonce, range(8), "5m", rows)
        elif arm == "primed8":
            burst(cl, nonce, [0], "5m", rows); burst(cl, nonce, range(1, 8), "5m", rows)
        elif arm == "ttl1h_600":
            rows.append(call(cl, nonce, 0, "1h")); time.sleep(600); rows.append(call(cl, nonce, 1, "1h"))
        res.append({"arm": arm, "rep": rep, "rows": rows})
    except Exception as e:
        res.append({"arm": arm, "rep": rep, "rows": rows, "error": type(e).__name__ + ": " + str(e)[:160]})
ARMS = ["burst8", "primed8", "ttl1h_600"]
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); res = []; th = []
    # ttl chains run in parallel with the others, but the burst arms are run one chain at a time so the bursts do not overlap each other
    for rep in range(3):
        x = threading.Thread(target=run_chain, args=(cl, "ttl1h_600", rep, res)); x.start(); th.append(x)
    for rep in range(3):
        for arm in ("burst8", "primed8"): run_chain(cl, arm, rep, res)
    for x in th: x.join()
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
def summarise(rows):
    out = {}
    for arm in ARMS:
        g = [r for r in rows if r["arm"] == arm and "error" not in r]
        if not g: continue
        allc = [u for r in g for u in r["rows"] if "error" not in u]
        out[arm] = {"chains": len(g), "calls": len(allc), "calls_with_read": sum(1 for u in allc if u["cr"] > 0),
                    "calls_with_write": sum(1 for u in allc if u["cw"] > 0),
                    "mean_cost_per_chain": sum(u["cost"] for u in allc) / len(g)}
    return out
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]
    print("chains", len(rows), "errors", sum("error" in r for r in rows))
    for a, s in summarise(rows).items():
        print(a, s)
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
