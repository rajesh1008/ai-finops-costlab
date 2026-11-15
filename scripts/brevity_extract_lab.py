#!/usr/bin/env python3
"""Ch11/Ch39 follow-up lab. REAL calls. Brevity instructions on extraction and classification tasks, with the FULL reply stored (the first brevity lab kept only 60 characters). 8 tasks, each with one checkable exact answer, 3 variants, 2 models, 2 repeats = 96 calls."""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
VARIANTS = {"none": "", "label_only": "Reply with the answer only, nothing else.", "label_why": "Reply with the answer, then one short sentence of reason."}
TASKS = [
 ("Classify the ticket as exactly one of BILLING, OUTAGE, ACCESS, OTHER.\nTicket: 'We were charged twice for the March usage and the invoice total does not match the dashboard.'", "BILLING"),
 ("Classify the ticket as exactly one of BILLING, OUTAGE, ACCESS, OTHER.\nTicket: 'Nobody on my team can log in since the SSO change this morning.'", "ACCESS"),
 ("Classify the ticket as exactly one of BILLING, OUTAGE, ACCESS, OTHER.\nTicket: 'The batch endpoint has returned 503 for every call since 09:10 UTC.'", "OUTAGE"),
 ("Classify the ticket as exactly one of BILLING, OUTAGE, ACCESS, OTHER.\nTicket: 'Can you send me the slide deck from last week's webinar?'", "OTHER"),
 ("Extract the invoice number from this text.\nText: 'Please find attached the statement for Q2. Reference INV-20931-B was paid on 14 June; INV-20977-C remains open.' Which invoice is still open?", "INV-20977-C"),
 ("Extract the monthly commitment amount in dollars as a plain integer.\nText: 'The customer agreed to a commitment of $48,000 per month for 12 months, with a $5,000 one-time onboarding fee.'", "48000"),
 ("Extract the model name that was deprecated.\nText: 'The platform team moved summarization from model-a to model-b in May. In October model-a was deprecated and model-c entered preview.'", "model-a"),
 ("Is the following statement about a cost report TRUE or FALSE? Answer with one word.\nStatement: 'A report showing $0 spend for a team that ran jobs all month proves the team is efficient.'", "FALSE"),
]
OUT = Path(__file__).resolve().parents[1] / "runs" / "brevity-extract-lab-2026-11-12.jsonl"
def one(a):
    cl, m, v, ti, rep = a
    q, exp = TASKS[ti]
    p = (q + "\n" + VARIANTS[v]).strip()
    x = cl.messages.create(model=m, max_tokens=1500, messages=[{"role": "user", "content": p}])
    reply = "".join(b.text for b in x.content if b.type == "text")
    ok = exp.lower() in reply.lower().replace(",", "")
    exact = reply.strip().strip(".").lower() == exp.lower()
    return {"model": m, "variant": v, "task": ti, "rep": rep, "input": x.usage.input_tokens, "out": x.usage.output_tokens, "stop": x.stop_reason, "ok": ok, "exact": exact, "reply": reply}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, v, t, r) for m in MODELS for v in VARIANTS for t in range(len(TASKS)) for r in range(2)]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"model": j[1], "variant": j[2], "task": j[3], "rep": j[4], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]
    print("calls:", len(rows), "errors:", sum("error" in r for r in rows))
    for m in MODELS:
        for v in VARIANTS:
            rs = [r for r in rows if r.get("model") == m and r.get("variant") == v and "error" not in r]
            if rs: print(f"{m:28s} {v:11s} n={len(rs)} mean_out={sum(r['out'] for r in rs)/len(rs):6.1f} mean_in={sum(r['input'] for r in rs)/len(rs):5.1f} correct={sum(r['ok'] for r in rs)} exact_format={sum(r['exact'] for r in rs)} not_end_turn={sum(r['stop']!='end_turn' for r in rs)}")
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
