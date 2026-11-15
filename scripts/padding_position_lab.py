#!/usr/bin/env python3
"""Chapter 19 lab (twentieth run). REAL calls. One fact (a retention period for a made-up product code) is hidden in a SYNTHETIC handbook padded with filler clauses
to about 1k, 4k, 16k and 48k tokens; the fact sits at the start, middle or end. 10 questions x 3 positions x 4 sizes x 2 models = 240 calls.
Records the billed input tokens, so cost per correct answer can be computed. Never prints the key."""
import os, sys, json, time, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "padding-position-lab-2026-11-11.json"
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]; SIZES = [20, 80, 320, 960]  # filler clauses; about 50 tokens each
def filler(i, rnd):
    return f"Clause {i}. For workspace tier {i % 7 + 1}, an agent must verify the account owner, note reference FS-{rnd.randint(1000, 9999)}, and confirm the review window of {30 + (i % 12) * 15} days before describing any procedure."
def main():
    rnd = random.Random(190); items = []
    for q in range(10):
        code = f"PX-{rnd.randint(100, 999)}"; days = rnd.choice([17, 23, 29, 41, 53, 67, 71, 89, 97, 113])
        items.append({"q": q, "code": code, "days": days, "fact": f"Special rule: product {code} keeps its archive for exactly {days} days and no other number applies to it."})
    cl = Anthropic(); jobs = [(it, n, pos, m) for it in items for n in SIZES for pos in ("start", "middle", "end") for m in MODELS]
    def run(job):
        it, n, pos, m = job; r = random.Random(1000 * it["q"] + n); fl = [filler(i, r) for i in range(n)]
        k = {"start": 0, "middle": n // 2, "end": n}[pos]; fl.insert(k, it["fact"]); doc = "\n".join(fl)
        prompt = f"{doc}\n\nQuestion: how many days does product {it['code']} keep its archive? Reply with the number only."
        for a in range(4):
            try:
                kw = {"thinking": {"type": "disabled"}} if "5-5" in m else {}
                x = cl.messages.create(model=m, max_tokens=20, messages=[{"role": "user", "content": prompt}], **kw)
                t = "".join(b.text for b in x.content if b.type == "text").strip()
                return {"q": it["q"], "n": n, "pos": pos, "model": m, "in": x.usage.input_tokens, "out": x.usage.output_tokens, "ans": t, "ok": t.strip(". ") == str(it["days"])}
            except Exception as e:
                err = type(e).__name__; time.sleep(2 + 3 * a)
        return {"q": it["q"], "n": n, "pos": pos, "model": m, "error": err}
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps(res)); print("saved", len(res), "errors", sum("error" in r for r in res))
if __name__ == "__main__": main()
