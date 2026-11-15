#!/usr/bin/env python3
"""Chapter 46 follow-up (nineteenth run), REAL calls plus an offline matcher. Six CANDIDATE vignettes (costlab/antipatterns_extra.py) are shown, with the thirty names and controls, to claude-haiku-4-5 and
claude-haiku-5-5 (thinking disabled), five repeats each, 60 calls. The model must pick one of A01..A30 or answer NONE if the vignette is not covered. Also prints the offline tf-idf nearest neighbour among the 30.
Output runs/antipattern-extra-lab-2026-11-11.json. Never prints the key."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.antipatterns import AP, tfidf_match
from costlab.antipatterns_extra import CAND
OUT = Path(__file__).resolve().parents[1] / "runs" / "antipattern-extra-lab-2026-11-11.json"
MODELS = {"h45": ("claude-haiku-4-5-20251001", {}), "h55": ("claude-haiku-5-5", {"thinking": {"type": "disabled"}})}
LIST = "\n".join(f"{a[0]}: {a[1]}. Control: {a[2]}" for a in AP)
def prompt(v): return (f"Here is a list of thirty AI cost anti-patterns:\n{LIST}\n\nVignette: {v}\n\nWhich anti-pattern does the vignette show? Reply with the ID only (for example A07), or NONE if no item in the list describes it.")
def one(cl, j):
    c, m, r = j; model, kw = MODELS[m]
    for att in range(4):
        try:
            x = cl.messages.create(model=model, max_tokens=20, messages=[{"role": "user", "content": prompt(CAND[c][4])}], **kw)
            t = "".join(b.text for b in x.content if b.type == "text").strip(); mm = re.search(r"A\d\d|NONE", t.upper().replace("A 0", "A0")); return {"c": CAND[c][0], "m": m, "rep": r, "answer": mm.group(0) if mm else "UNPARSED", "raw": t[:40]}
        except (APIStatusError, APIConnectionError): time.sleep(2 * (att + 1))
    return {"c": CAND[c][0], "m": m, "rep": r, "answer": "ERROR", "raw": ""}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(c, m, r) for c in range(len(CAND)) for m in MODELS for r in range(5)]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(lambda j: one(cl, j), jobs))
    docs = [a[1] + " " + a[2] for a in AP]; nn = {c[0]: AP[tfidf_match(c[4], docs)][0] for c in CAND}
    OUT.write_text(json.dumps({"results": res, "tfidf_nearest": nn})); print("saved", OUT.name, len(res), "errors", sum(r["answer"] == "ERROR" for r in res)); print("tfidf nearest:", nn)
if __name__ == "__main__": main()
