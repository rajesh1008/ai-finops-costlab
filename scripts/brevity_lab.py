#!/usr/bin/env python3
"""Chapter 11 and 39 lab. REAL calls. Does a one-line brevity instruction cut billed output tokens, and does it cost correctness? 10 questions with a single checkable answer (computed here, never judged by a model), 4 instruction variants, 2 models, 2 repeats, max_tokens 1500."""
import os, sys, json, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
VARIANTS = {"none": "", "brief": "Be brief.", "one_line": "Answer in one line, then stop.", "answer_only": "Reply with the final answer only, no explanation."}
QS = [("A job uses 3,400 input tokens at $1.00 per million and 900 output tokens at $5.00 per million. What is its cost in dollars? Give the number to five decimals.", "0.00790"),
      ("What is 17 percent of 2,450? ", "416.5"),
      ("A cache read costs 10 percent of the base input price of $3.00 per million tokens. What is the price of 2 million cached tokens read, in dollars?", "0.60"),
      ("A team spends $18,400 in a month with 23 working days. What is the average spend per working day, in dollars, to the nearest dollar?", "800"),
      ("If output tokens cost five times input tokens and input costs $0.80 per million, what is the output price per million in dollars?", "4.00"),
      ("A batch discount of 50 percent applies to a $1,260 monthly bill. What is the discounted bill in dollars?", "630"),
      ("1,200 requests a day at $0.0045 each for 30 days. Total in dollars?", "162"),
      ("A prompt of 12,000 tokens is sent 40 times. How many input tokens in total?", "480000"),
      ("Spend went from $52,000 to $65,000. What is the percentage increase?", "25"),
      ("An agent takes 9 steps and each step re-sends 2,500 more tokens than the last, starting at 2,500 tokens on step one. What is the total number of input tokens across all steps?", "112500")]
OUT = Path(__file__).resolve().parents[1] / "runs" / "brevity-lab-2026-11-12.jsonl"
def ok(reply, exp):
    t = reply.replace(",", "").replace("*", " ").replace("$", " ")
    nums = re.findall(r"\d+(?:\.\d+)?", t)
    e = float(exp)
    return any(abs(float(n) - e) < 1e-9 for n in nums)
def one(a):
    cl, m, v, qi, rep = a
    q, exp = QS[qi]
    p = (q.strip() + " " + VARIANTS[v]).strip()
    x = cl.messages.create(model=m, max_tokens=1500, messages=[{"role": "user", "content": p}])
    reply = "".join(b.text for b in x.content if b.type == "text")
    return {"model": m, "variant": v, "q": qi, "rep": rep, "input": x.usage.input_tokens, "out": x.usage.output_tokens, "stop": x.stop_reason, "ok": ok(reply, exp), "tail": reply[-60:]}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, v, q, r) for m in MODELS for v in VARIANTS for q in range(len(QS)) for r in range(2)]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"model": j[1], "variant": j[2], "q": j[3], "rep": j[4], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summarise(rows):
    res = {}
    for m in MODELS:
        for v in VARIANTS:
            rs = [r for r in rows if r.get("model") == m and r.get("variant") == v and "error" not in r]
            if rs: res[(m, v)] = (len(rs), sum(r["out"] for r in rs) / len(rs), sum(r["ok"] for r in rs), sum(r["stop"] != "end_turn" for r in rs))
    return res
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        rows = [json.loads(l) for l in OUT.read_text().splitlines()]
        print("errors:", sum("error" in r for r in rows))
        for (m, v), (n, mo, c, nt) in summarise(rows).items(): print(f"{m:28s} {v:12s} n={n:3d} mean_out={mo:7.1f} correct={c}/{n} not_end_turn={nt}")
    else: main()
