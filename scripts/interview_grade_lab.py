#!/usr/bin/env python3
"""Chapter 47 lab, REAL calls. 40 triples sampled (seed 11) from the book's own Q&A sections. Pairwise: the model sees a question and two answers and says which is better, A or B.
Conditions: F (full strong vs weak), T (strong truncated to its first sentence vs weak). Both orders. 2 models x 2 conditions x 40 x 2 orders = 320 calls. Output runs/interview-grade-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.interviewgrade import extract, sample, first_sentence
ROOT = Path(__file__).resolve().parents[3]; OUT = Path(__file__).resolve().parents[1] / "runs" / "interview-grade-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
def prompt(q, a, b): return f"You are a hiring manager for an AI FinOps role. Interview question: {q}\n\nAnswer A: {a}\n\nAnswer B: {b}\n\nWhich answer is better? Reply with A or B only."
def call(cl, model, kw, text):
    for att in range(4):
        try:
            r = cl.messages.create(model=model, max_tokens=10, messages=[{"role": "user", "content": text}], **kw)
            return "".join(b.text for b in r.content if b.type == "text").strip()
        except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
    return None
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    T = sample(extract(str(ROOT / "02-manuscript" / "ch*.md")), 40); cl = Anthropic()
    jobs = [(m, c, i, o) for m in MODELS for c in "FT" for i in range(len(T)) for o in (0, 1)]
    def one(j):
        m, c, i, o = j; t = T[i]; strong = t["strong"] if c == "F" else first_sentence(t["strong"]); weak = t["weak"]
        a, b = (strong, weak) if o == 0 else (weak, strong)
        r = call(cl, MODELS[m][0], MODELS[m][1], prompt(t["q"], a, b)); ch = r[:1] if r else None
        picked = None if ch not in ("A", "B") else ("strong" if (ch == "A") == (o == 0) else "weak")
        return {"m": m, "cond": c, "i": i, "file": t["file"], "order": o, "choice": ch, "picked": picked, "len_strong": len(strong), "len_weak": len(weak)}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res, "triples": [{"file": t["file"], "q": t["q"]} for t in T]})); print("saved", OUT.name, len(res), "unparsed", sum(r["picked"] is None for r in res))
if __name__ == "__main__": main()
