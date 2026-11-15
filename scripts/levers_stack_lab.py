#!/usr/bin/env python3
"""Chapter 43 lab, REAL calls. 120 SYNTHETIC handbook questions (seed 431) answered under four arms:
A0 whole handbook in the prompt, claude-haiku-4-5, no cache; A0c same with the handbook block cached (cache_control ephemeral), run sequentially so reads can hit;
A1 BM25 top 3 clauses, claude-haiku-4-5; A2 BM25 top 3, claude-haiku-5-5 (thinking disabled). 480 calls. Records every usage field the bill is made from. Output runs/levers-stack-lab-2026-11-11.json."""
import os, sys, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.retrieval import BM25
from costlab.ladder import clauses, make_questions, score
OUT = Path(__file__).resolve().parents[1] / "runs" / "levers-stack-lab-2026-11-11.json"
H45, H55 = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
SYS = "You answer questions about the Fieldstone support handbook using only the clauses supplied. Reply in one short sentence. If the supplied clauses do not contain what is needed, say you cannot answer."
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); C = clauses(); bm = BM25([c["text"] for c in C]); Q = make_questions(120, 431)
    whole = "Clauses:\n" + "\n".join(c["text"] for c in C)
    def call(i, q, arm):
        model, kw = (H55, {"thinking": {"type": "disabled"}}) if arm == "A2" else (H45, {})
        if arm in ("A0", "A0c"): ctx = whole
        else: ctx = "Clauses:\n" + "\n".join(C[t]["text"] for t in bm.search(q["q"], 3))
        if arm == "A0c": content = [{"type": "text", "text": ctx, "cache_control": {"type": "ephemeral"}}, {"type": "text", "text": f"Question: {q['q']}"}]
        else: content = f"{ctx}\n\nQuestion: {q['q']}"
        err = None
        for att in range(4):
            try:
                r = cl.messages.create(model=model, max_tokens=200, system=SYS, messages=[{"role": "user", "content": content}], **kw)
                txt = "".join(b.text for b in r.content if b.type == "text"); u = r.usage
                return {"i": i, "t": q["t"], "arm": arm, "in": u.input_tokens, "out": u.output_tokens, "cr": getattr(u, "cache_read_input_tokens", 0) or 0,
                        "cw": getattr(u, "cache_creation_input_tokens", 0) or 0, "text": txt[:200], "ok": score(txt, q["gold"]), "error": None}
            except (APIStatusError, APIConnectionError) as e:
                err = f"{type(e).__name__}:{getattr(e, 'status_code', None)}"; time.sleep(2 * (att + 1))
        return {"i": i, "t": q["t"], "arm": arm, "in": 0, "out": 0, "cr": 0, "cw": 0, "text": "", "ok": False, "error": err}
    res = []
    with ThreadPoolExecutor(6) as ex:
        res += list(ex.map(lambda j: call(*j), [(i, q, a) for i, q in enumerate(Q) for a in ("A0", "A1", "A2")]))
    res.append(call(0, Q[0], "A0c"))  # first call writes the cache
    for i, q in enumerate(Q):
        if i: res.append(call(i, q, "A0c"))
    OUT.write_text(json.dumps({"results": res})); print("saved", OUT.name, len(res), "errors", sum(1 for r in res if r["error"]))
if __name__ == "__main__": main()
