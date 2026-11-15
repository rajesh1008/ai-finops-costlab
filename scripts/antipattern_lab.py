#!/usr/bin/env python3
"""Chapter 46 lab, REAL calls. 30 author-written vignettes; each model is shown the list of 30 anti-pattern names (condition N) or the 30 controls (condition C), with ids, and asked for the single best id.
2 models x 2 conditions x 30 vignettes x 2 reps = 240 calls. Output runs/antipattern-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.antipatterns import AP
OUT = Path(__file__).resolve().parents[1] / "runs" / "antipattern-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
LIST_N = "\n".join(f"{a[0]}: {a[1]}" for a in AP); LIST_C = "\n".join(f"{a[0]}: {a[2]}" for a in AP)
def prompt(cond, v):
    lst, what = (LIST_N, "anti-pattern") if cond == "N" else (LIST_C, "control")
    return f"Here are thirty {what}s in AI cost management, each with an id.\n\n{lst}\n\nRead this situation.\n\n{v}\n\nWhich single {what} fits it best? Reply with the id only, for example A07."
def call(cl, model, kw, text):
    for att in range(4):
        try:
            r = cl.messages.create(model=model, max_tokens=20, messages=[{"role": "user", "content": text}], **kw)
            return "".join(b.text for b in r.content if b.type == "text"), r.usage.input_tokens, r.usage.output_tokens
        except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
    return None
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(m, c, a[0], a[4], r) for m in MODELS for c in "NC" for a in AP for r in range(2)]
    def one(j):
        m, c, aid, v, r = j; res = call(cl, MODELS[m][0], MODELS[m][1], prompt(c, v))
        txt = res[0] if res else ""; mm = re.search(r"A\d\d", txt)
        return {"m": m, "cond": c, "truth": aid, "rep": r, "pred": mm.group(0) if mm else None, "raw": txt[:30], "tin": res[1] if res else None, "tout": res[2] if res else None, "api_error": res is None}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "api_errors", sum(r["api_error"] for r in res))
if __name__ == "__main__": main()
