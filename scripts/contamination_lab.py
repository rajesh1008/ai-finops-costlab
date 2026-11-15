#!/usr/bin/env python3
"""Chapter 22 lab. REAL calls, claude-haiku-4-5. 60 SYNTHETIC billing problems (seed 17, exact answers), two samples each, three conditions:
 clean    the problem alone (a clean restart)
 same     the problem, a plausible WRONG earlier attempt (refund taken at the undiscounted price), 'that was marked incorrect, try again'
 same_log the same plus a 1,500-token failed tool log the harness left in the context
 same_nofb the wrong attempt in context, then only 'Please double-check and answer again.' (no statement that it was wrong)
 clean_hint a clean context that states 'an earlier answer of $X was marked incorrect' but carries no attempt text
Default temperature. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
from costlab.cascade import make_problems, correct
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "contamination-lab-2026-11-10.json"
MODEL = "claude-haiku-4-5-20251001"
def wrong_attempt(q, p):
    import re
    s, price, d, r = None, None, None, None
    m = re.search(r"\$(\d+) per seat for (\d+) seats, then given a (\d+) percent discount.*refunded for (\d+) seats", q)
    price, s, d, r = (int(x) for x in m.groups())
    wrong = round(s * price * (1 - d / 100) - r * price, 2)
    return (f"Total after discount: {s} x ${price} x {1 - d/100:.2f} = ${s*price*(1-d/100):.2f}. Refund: {r} seats at ${price} = ${r*price:.2f}. "
            f"Net amount charged: ${wrong:.2f}."), wrong
LOG = "\n".join(f"[tool:billing_ledger] attempt {i} -> HTTP 503 upstream timeout after 30s; retry-after header absent; trace id fs-{7000+i*37}" for i in range(1, 36))
def msgs(cond, q, p):
    if cond == "clean": return [{"role": "user", "content": q}]
    att, w = wrong_attempt(q, p)
    if cond == "clean_hint": return [{"role": "user", "content": q + f"\n\nAn earlier answer of ${w:.2f} was marked incorrect. Give the correct net amount and one sentence."}]
    if cond == "same_nofb": return [{"role": "user", "content": q}, {"role": "assistant", "content": att}, {"role": "user", "content": "Please double-check and answer again, giving the net amount and one sentence."}]
    first = q if cond == "same" else q + "\n\nHarness log from the earlier run:\n" + LOG
    return [{"role": "user", "content": first}, {"role": "assistant", "content": att},
            {"role": "user", "content": "That was marked incorrect. Try again and give the net amount and one sentence."}]
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    c = Anthropic(); P = make_problems(60)
    jobs = [(cond, p, j) for p in P for cond in ("clean", "same", "same_log", "same_nofb", "clean_hint") for j in range(2)]
    def run(job):
        cond, p, j = job
        for a in range(4):
            try:
                m = c.messages.create(model=MODEL, max_tokens=300, messages=msgs(cond, p["q"], p))
                t = "".join(x.text for x in m.content if x.type == "text")
                return {"cond": cond, "id": p["id"], "j": j, "ok": correct(t, p["answer"]), "in": m.usage.input_tokens, "out": m.usage.output_tokens,
                        "repeat_wrong": wrong_attempt(p["q"], p)[1] in [float(x) for x in __import__("re").findall(r"\d+\.\d+", t.replace(",", ""))] and not correct(t, p["answer"])}
            except Exception as e: time.sleep(2 + 3 * a)
        return {"cond": cond, "id": p["id"], "j": j, "ok": None}
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps(res)); print("saved", OUT.name, "failed calls:", sum(1 for r in res if r["ok"] is None))
if __name__ == "__main__": main()
