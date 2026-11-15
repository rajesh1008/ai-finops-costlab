#!/usr/bin/env python3
"""Chapter 19 follow-up lab (twentieth run), written after padding_position_lab.py returned 100 percent everywhere. REAL calls.
Harder: the document holds an old rule and an amendment that replaces it, plus a near-miss code (one digit different) with its own number.
Order A: old rule early, amendment late. Order B: amendment early, old rule late (the stale-later trap). Sizes 80, 320, 960 filler clauses. 10 q x 3 x 2 x 2 models = 120 calls."""
import os, sys, json, time, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "padding-amend-lab-2026-11-11.json"
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]; SIZES = [80, 320, 960]
def filler(i, r): return f"Clause {i}. For workspace tier {i % 7 + 1}, an agent must verify the account owner, note reference FS-{r.randint(1000, 9999)}, and confirm the review window of {30 + (i % 12) * 15} days before describing any procedure."
def main():
    rnd = random.Random(191); items = []
    for q in range(10):
        c = rnd.randint(100, 989); old, new, near = rnd.sample(range(10, 120), 3)
        items.append({"q": q, "code": f"PX-{c}", "near": f"PX-{c + 1}", "old": old, "new": new, "nearv": near})
    cl = Anthropic(); jobs = [(it, n, o, m) for it in items for n in SIZES for o in "AB" for m in MODELS]
    def run(job):
        it, n, o, m = job; r = random.Random(7000 * it["q"] + n); fl = [filler(i, r) for i in range(n)]
        old = f"Rule R-{it['q']}: product {it['code']} keeps its archive for {it['old']} days."
        new = f"Amendment to rule R-{it['q']}: the period for product {it['code']} is now {it['new']} days, replacing the earlier figure."
        near = f"Rule N-{it['q']}: product {it['near']} keeps its archive for {it['nearv']} days."
        a, b = (old, new) if o == "A" else (new, old)
        fl.insert(n // 10, a); fl.insert(n // 2, near); fl.insert(n, b)
        prompt = "\n".join(fl) + f"\n\nQuestion: what is the current archive period in days for product {it['code']}? Reply with the number only."
        for t in range(4):
            try:
                kw = {"thinking": {"type": "disabled"}} if "5-5" in m else {}
                x = cl.messages.create(model=m, max_tokens=20, messages=[{"role": "user", "content": prompt}], **kw)
                s = "".join(k.text for k in x.content if k.type == "text").strip().strip(". ")
                return {"q": it["q"], "n": n, "order": o, "model": m, "in": x.usage.input_tokens, "out": x.usage.output_tokens, "ans": s, "ok": s == str(it["new"]), "stale": s == str(it["old"]), "near": s == str(it["nearv"])}
            except Exception as e: err = type(e).__name__; time.sleep(2 + 3 * t)
        return {"q": it["q"], "n": n, "order": o, "model": m, "error": err}
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(run, jobs))
    OUT.write_text(json.dumps(res)); print("saved", len(res), "errors", sum("error" in r for r in res))
if __name__ == "__main__": main()
