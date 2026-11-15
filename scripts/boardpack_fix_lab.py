#!/usr/bin/env python3
"""Chapter 40 follow-up lab, REAL calls. The fix the board line pointed at: the same 200 questions (seed 401), claude-haiku-5-5 thinking disabled, but retrieval also pulls every clause named by 'escalate per clause N' in the top 3 clauses (generic expansion, up to 3 extra clauses, no use of the question template or the gold answer).
Output runs/boardpack-fix-lab-2026-11-11.json. Written AFTER the first lab showed template C failing; disclosed in the chapter."""
import os, sys, json, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "boardpack-fix-lab-2026-11-11.json"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(200, 401)
    def one(iq):
        i, q = iq; top = list(bm.search(q["q"], 3)); extra = []
        for t in top:
            m = re.search(r"escalate per clause (\d+)", C[t]["text"])
            if m and int(m.group(1)) - 1 not in top and int(m.group(1)) - 1 not in extra: extra.append(int(m.group(1)) - 1)
        ctx = "\n".join(C[t]["text"] for t in top + extra[:3])
        for att in range(4):
            try:
                r = cl.messages.create(model="claude-haiku-5-5", max_tokens=200, system=SYS, thinking={"type": "disabled"}, messages=[{"role": "user", "content": f"Clauses:\n{ctx}\n\nQuestion: {q['q']}"}])
                txt = "".join(b.text for b in r.content if b.type == "text")
                return {"i": i, "t": q["t"], "m": "M2x", "in": r.usage.input_tokens, "out": r.usage.output_tokens, "text": txt[:200], "ok": score(txt, q["gold"]), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
        return {"i": i, "t": q["t"], "m": "M2x", "in": 0, "out": 0, "text": "", "ok": False, "error": err}
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, enumerate(Q)))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
