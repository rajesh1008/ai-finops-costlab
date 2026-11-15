#!/usr/bin/env python3
"""Chapter 47 second follow-up lab (nineteenth run, cross-model), REAL calls. The same 40 triples as interview_grade_lab.py (seed 11).
Stage 1: claude-haiku-5-5 (thinking disabled) WRITES a plausible weak answer for each question: about the same length as the strong answer, same vocabulary, confident, one specific flaw a real candidate might have.
Stage 2: pairwise grading, strong against the generated weak answer, both orders, both models (thinking disabled on haiku-5-5). 40 + 160 calls. Output runs/interview-plausible-h55gen-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.interviewgrade import extract, sample, words
ROOT = Path(__file__).resolve().parents[3]; OUT = Path(__file__).resolve().parents[1] / "runs" / "interview-plausible-h55gen-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
def call(cl, model, kw, text, mx):
    for att in range(4):
        try:
            r = cl.messages.create(model=model, max_tokens=mx, messages=[{"role": "user", "content": text}], **kw)
            return "".join(b.text for b in r.content if b.type == "text").strip()
        except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
    return None
def gen_prompt(q, strong): return (f"Interview question for an AI FinOps role: {q}\n\nHere is a strong answer ({len(words(strong))} words):\n{strong}\n\n"
    f"Write a plausible but flawed answer to the same question, as a real candidate might give it. It must be within 20 percent of the strong answer's length, use the same vocabulary and a believable structure, sound confident, and contain exactly one specific substantive flaw (for example a saving that is not measured against a baseline, a metric with no quality bar, a total reconciled to the invoice and nothing else, or a number with no limit). Do not signal the flaw. Reply with the answer text only.")
def grade_prompt(q, a, b): return f"You are a hiring manager for an AI FinOps role. Interview question: {q}\n\nAnswer A: {a}\n\nAnswer B: {b}\n\nWhich answer is better? Reply with A or B only."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    T = sample(extract(str(ROOT / "02-manuscript" / "ch*.md")), 40); cl = Anthropic()
    m4, k4 = MODELS["h55"]
    with ThreadPoolExecutor(6) as ex: gens = list(ex.map(lambda t: call(cl, m4, k4, gen_prompt(t["q"], t["strong"]), 700), T))
    ok = [i for i, g in enumerate(gens) if g]
    jobs = [(m, i, o) for m in MODELS for i in ok for o in (0, 1)]
    def one(j):
        m, i, o = j; t = T[i]; a, b = (t["strong"], gens[i]) if o == 0 else (gens[i], t["strong"])
        r = call(cl, MODELS[m][0], MODELS[m][1], grade_prompt(t["q"], a, b), 10); ch = r[:1] if r else None
        picked = None if ch not in ("A", "B") else ("strong" if (ch == "A") == (o == 0) else "weak")
        return {"m": m, "i": i, "file": t["file"], "order": o, "choice": ch, "picked": picked}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"results": res, "weak": gens, "len_strong": [len(words(t["strong"])) for t in T], "len_weak": [len(words(g)) if g else None for g in gens], "q": [t["q"] for t in T]}))
    print("saved", OUT.name, len(res), "gens", len(ok), "unparsed", sum(r["picked"] is None for r in res))
if __name__ == "__main__": main()
