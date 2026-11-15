#!/usr/bin/env python3
"""Chapter 29 lab, REAL calls. Items: the 300 incumbent answers recorded by shadow_lab.py, plus 150 SYNTHETIC corruptions (a correct incumbent answer whose retention window is replaced by a different number; intended to be wrong; one of them still passes the scorer because the original named a different clause).
Gold label for every item: the exact scorer in costlab.ladder. Four judge configurations, each given one item at a time:
  ctx_h5   claude-haiku-5-5, verdict only, sees the handbook clauses that hold the true values, no reference answer
  ctx_h4   claude-haiku-4-5, same prompt
  ref_h5   claude-haiku-5-5, verdict only, sees the reference answer (gold) instead of clauses
  cot_h5   claude-haiku-5-5, same as ctx_h5 but asked to explain in two sentences before the verdict (max 300 output tokens)
  think_h5 claude-haiku-5-5 with thinking left at the model default, verdict-only prompt, max 700 output tokens
Thinking is explicitly disabled (thinking={'type':'disabled'}) for the other haiku-5-5 configurations: in a first run with max_tokens 24 the model spent the budget on a thinking block and returned no verdict for 117 of 450 ctx_h5 calls.
Errors are recorded. No temperature argument. Key from the environment, never printed."""
import os, sys, re, json, time, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anthropic import Anthropic, APIStatusError, APIConnectionError
from costlab.ladder import clauses, score
RUNS = Path(__file__).resolve().parents[1] / "runs"; OUT = RUNS / "judge-lab-2026-11-10.json"
H4, H5 = "claude-haiku-4-5-20251001", "claude-haiku-5-5"
CONF = {"ctx_h5": (H5, "ctx", 24, False), "ctx_h4": (H4, "ctx", 24, False), "ref_h5": (H5, "ref", 24, False), "cot_h5": (H5, "ctx", 300, False), "think_h5": (H5, "ctx", 700, True)}  # last field: thinking left at the model default (True) or disabled (False; sent only to haiku-5-5)
SYS = "You grade answers to questions about the Fieldstone support handbook. An answer is CORRECT only if every code and number it states for the question asked matches the evidence. Wrong or missing values are INCORRECT."
def corrupt(ans, gold):
    for g in gold:
        if not g.startswith("FS-") and re.search(rf"(?<![\d-]){g}(?![\d])", ans): return re.sub(rf"(?<![\d-]){g}(?![\d])", str(int(g) + 15), ans, count=1)
    return None
def main():
    sh = json.load(open(RUNS / "shadow-lab-2026-11-10.json")); Q = sh["questions"]; C = clauses(); rnd = random.Random(291)
    inc = [r for r in sh["results"] if r["model"] == sh["models"]["incumbent"] and r["error"] is None]
    items = [{"q": r["q"], "answer": r["answer"], "kind": "recorded", "gold_ok": score(r["answer"], Q[r["q"]]["gold"])} for r in inc]
    good = [r for r in inc if r["ok"]]; rnd.shuffle(good)
    for r in good[:150]:
        c = corrupt(r["answer"], Q[r["q"]]["gold"])
        if c: items.append({"q": r["q"], "answer": c, "kind": "corrupted", "gold_ok": score(c, Q[r["q"]]["gold"])})
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic()
    def evidence(q, mode):
        if mode == "ref": return "Reference answer values: " + ", ".join(Q[q]["gold"])
        need = Q[q]["needs"]; return "Handbook clauses:\n" + "\n".join(C[i - 1]["text"] for i in need)
    def one(job):
        k, name = job; it = items[k]; model, mode, mt, think = CONF[name]; extra = {} if (think or model == H4) else {"thinking": {"type": "disabled"}}; q = Q[it["q"]]
        tail = "Reply with exactly one word: CORRECT or INCORRECT." if name != "cot_h5" else "Explain in at most two sentences, then end with a final line 'VERDICT: CORRECT' or 'VERDICT: INCORRECT'."
        msg = f"{evidence(it['q'], mode)}\n\nQuestion: {q['q']}\nAnswer to grade: {it['answer']}\n\n{tail}"; att = 0
        while True:
            att += 1
            try:
                m = cl.messages.create(model=model, max_tokens=mt, system=SYS, messages=[{"role": "user", "content": msg}], **extra)
                t = "".join(b.text for b in m.content if b.type == "text"); up = t.upper()
                v = ("INCORRECT" if "INCORRECT" in up.split("VERDICT:")[-1] else "CORRECT" if "CORRECT" in up.split("VERDICT:")[-1] else None) if "VERDICT:" in up else ("INCORRECT" if "INCORRECT" in up else "CORRECT" if "CORRECT" in up else None)
                return {"item": k, "judge": name, "in": m.usage.input_tokens, "out": m.usage.output_tokens, "verdict": v, "stop": m.stop_reason, "error": None, "attempts": att}
            except (APIStatusError, APIConnectionError) as e:
                code = getattr(e, "status_code", None)
                if att < 4 and (code in (429, 500, 502, 503, 529) or code is None): time.sleep(2 * att); continue
                return {"item": k, "judge": name, "in": 0, "out": 0, "verdict": None, "stop": None, "error": f"{type(e).__name__}: {str(e)[:160]}", "attempts": att}
    jobs = [(k, n) for k in range(len(items)) for n in CONF]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text(json.dumps({"items": items, "judges": {n: list(v) for n, v in CONF.items()}, "results": res}))
    print("saved", OUT.name, "items", len(items), "calls", len(res), "errors", sum(r["error"] is not None for r in res), "no_verdict", sum(r["verdict"] is None and r["error"] is None for r in res))
if __name__ == "__main__": main()
