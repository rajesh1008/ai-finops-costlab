#!/usr/bin/env python3
"""Chapters 19 and 24 lab. REAL calls. A synthetic 14-step agent run (each step is a tool call with a result of about 500 tokens, written from a seeded generator) ends with a question about a fact that appeared at a known step. Four ways of presenting the history at step 15: full transcript; window (last 4 steps only); digest (one deterministic line per step: step, tool, key id, no detail); model summary (one extra call per model and repeat that writes a summary of steps 1-10, then steps 11-14 verbatim). Three questions: a fact from step 3 that is carried in the digest line (the refund id), a fact from step 3 that is NOT in the digest line (the carrier reference inside the result body), and a fact from step 13 (inside the window). Exact-match scoring against values computed from the generator, never model judged. max_tokens 300, no tools. Summary-call tokens are billed and counted against the summary variant."""
import os, sys, json, random, time
from pathlib import Path
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
VARIANTS = ["full", "window", "digest", "model_summary"]
REPEATS = 3
MAX_TOKENS = 300
STEPS = 14
SUMMARY_MAX = int(os.environ.get("LAB_SUMMARY_MAX", "500"))
if os.environ.get("LAB_MODELS"): MODELS = os.environ["LAB_MODELS"].split(",")
OUT = Path(__file__).resolve().parents[1] / "runs" / os.environ.get("LAB_OUT", "compaction-lab-2026-11-12.jsonl")
TOOLS = ["lookup_order", "check_stock", "issue_refund", "get_carrier_status", "read_policy", "search_tickets"]
def make_steps(seed=11):
    r = random.Random(seed); steps = []
    for i in range(1, STEPS + 1):
        tool = TOOLS[(i * 5 + r.randint(0, 2)) % len(TOOLS)]
        key = f"{tool[:3].upper()}-{r.randint(10000, 99999)}"
        carrier = f"CR{r.randint(100000, 999999)}"
        filler = " ".join(f"{r.choice(['field','record','entry','note','value','flag'])}{r.randint(1,99)}={r.randint(100,9999)}" for _ in range(70))
        body = f"result for step {i}: id {key}; carrier reference {carrier}; {filler}"
        steps.append({"n": i, "tool": tool, "key": key, "carrier": carrier, "body": body})
    return steps
def full_text(steps): return "\n".join(f"[step {s['n']}] tool={s['tool']} -> {s['body']}" for s in steps)
def digest_text(steps): return "\n".join(f"[step {s['n']}] tool={s['tool']} id={s['key']}" for s in steps)
def questions(steps):
    s3, s13 = steps[2], steps[12]
    return [(f"What id did the tool return at step 3? Reply with the id only.", s3["key"]),
            (f"What was the carrier reference in the result at step 3? Reply with the reference only.", s3["carrier"]),
            (f"What was the carrier reference in the result at step 13? Reply with the reference only.", s13["carrier"])]
def history(variant, steps, summary=""):
    if variant == "full": return full_text(steps)
    if variant == "window": return full_text(steps[-4:])
    if variant == "digest": return digest_text(steps[:-4]) + "\n" + full_text(steps[-4:])
    if variant == "model_summary": return "Summary of steps 1-10: " + summary + "\n" + full_text(steps[-4:])
    raise ValueError(variant)
def prompt(h, q): return f"Below is the record of a support agent's run so far.\n\n{h}\n\nQuestion: {q}"
def correct(reply, expected):
    t = reply.lower().replace("*", " ").replace(",", "")
    return expected.lower() in [w.strip(".:;()\"'`") for w in t.split()]
def summarise(rows):
    res = {}
    for m in sorted({r["model"] for r in rows}):
        res[m] = {}
        for v in VARIANTS:
            rs = [r for r in rows if r["model"] == m and r["variant"] == v]
            if not rs: continue
            res[m][v] = {"n": len(rs), "mean_input": sum(r["input"] for r in rs) / len(rs), "mean_summary_tokens": sum(r.get("summary_in", 0) + r.get("summary_out", 0) for r in rs) / len(rs),
                         "correct": sum(r["ok"] for r in rs), "correct_by_q": [sum(r["ok"] for r in rs if r["q"] == q) for q in sorted({r["q"] for r in rs})]}
    return res
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); steps = make_steps(); qs = questions(steps); out = []
    for m in MODELS:
        for rep in range(REPEATS):
            sx = cl.messages.create(model=m, max_tokens=SUMMARY_MAX, messages=[{"role": "user", "content": "Summarise this agent record for a colleague who will continue the run. Keep what is needed to continue; be brief.\n\n" + full_text(steps[:10])}])
            summary = "".join(b.text for b in sx.content if b.type == "text")
            su = sx.usage
            for v in VARIANTS:
                for qi, (q, exp) in enumerate(qs):
                    x = cl.messages.create(model=m, max_tokens=MAX_TOKENS, messages=[{"role": "user", "content": prompt(history(v, steps, summary), q)}])
                    reply = "".join(b.text for b in x.content if b.type == "text"); u = x.usage
                    row = {"model": m, "variant": v, "q": qi, "rep": rep, "input": u.input_tokens, "output": u.output_tokens, "stop": x.stop_reason, "ok": correct(reply, exp), "reply": reply[-80:]}
                    if v == "model_summary": row.update(summary_in=su.input_tokens, summary_out=su.output_tokens, summary_chars=len(summary), summary_stop=sx.stop_reason)
                    out.append(row); time.sleep(0.2)
    OUT.write_text("\n".join(json.dumps(r) for r in out) + "\n")
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        rows = [json.loads(l) for l in OUT.read_text().splitlines()]
        for m, d in summarise(rows).items():
            for v, s in d.items(): print(m, v, "n", s["n"], "mean_input %.0f" % s["mean_input"], "summary_tokens %.0f" % s["mean_summary_tokens"], "correct", s["correct"], "/", s["n"], "by_q", s["correct_by_q"])
    else: main()
