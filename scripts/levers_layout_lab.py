#!/usr/bin/env python3
"""Chapter 43 follow-up, REAL calls (written after seeing A0 at 94 and A0c at 110 correct of 120). Same 120 questions (seed 431), claude-haiku-4-5, whole handbook:
R  rerun of A0 exactly as before (noise check); S  question in a separate content block as in A0c but with NO cache_control (layout check). 240 calls.
Output runs/levers-layout-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "levers-layout-lab-2026-11-11.json"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); C = clauses(); Q = make_questions(120, 431); whole = "Clauses:\n" + "\n".join(c["text"] for c in C)
    def call(j):
        i, q, arm = j
        content = f"{whole}\n\nQuestion: {q['q']}" if arm == "R" else [{"type": "text", "text": whole}, {"type": "text", "text": f"Question: {q['q']}"}]
        err = None
        for att in range(4):
            try:
                r = cl.messages.create(model="claude-haiku-4-5-20251001", max_tokens=200, system=SYS, messages=[{"role": "user", "content": content}])
                txt = "".join(b.text for b in r.content if b.type == "text")
                return {"i": i, "t": q["t"], "arm": arm, "in": r.usage.input_tokens, "out": r.usage.output_tokens, "text": txt[:200], "ok": score(txt, q["gold"]), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
        return {"i": i, "t": q["t"], "arm": arm, "in": 0, "out": 0, "text": "", "ok": False, "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(call, [(i, q, a) for i, q in enumerate(Q) for a in ("R", "S")]))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
