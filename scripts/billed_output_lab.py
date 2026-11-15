#!/usr/bin/env python3
"""Chapter 17 / Chapter 12 lab (twenty-first run). REAL calls. Same 12 prompts, 3 repeats, both models, ceiling 4000. Records billed output tokens against visible text length and block types, to show that a per-token price is not a per-call cost when one model reasons before it answers. Prompts are mine."""
import os, sys, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
OUT = Path(__file__).resolve().parents[1] / "runs" / "billed-output-lab-2026-11-11.jsonl"
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
P = {
 "classify": ["Classify this ticket as billing, bug or how-to. Reply with one word. Ticket: 'I was charged twice for March and need one refund.'", "Classify this ticket as billing, bug or how-to. Reply with one word. Ticket: 'The export button does nothing after I pick a date range.'"],
 "extract": ["From this text give only the invoice number: 'Please see invoice INV-20418 dated 3 March for the overdue balance.'", "From this text give only the amount in dollars: 'The approved refund is 142 dollars after a prior credit of 30.'"],
 "arith": ["A job makes 4,200 calls a day with 1,900 input and 310 output tokens per call at $1 per million input and $5 per million output. What does it cost per day? Reply with the figure and one line of working.", "Cost per resolved ticket: spend $9,300, 4,650 tickets, 62 percent resolved. Give cost per resolved ticket to the cent, one line of working."],
 "short_explain": ["In two sentences, say why a cache hit rate can fall after a prompt edit.", "In two sentences, say why average cost per user hides loss-making customers."],
 "judgement": ["Should a team with a $3,000 a month AI bill build a custom router? Answer in at most 80 words.", "Is a 15 percent discount for a 12 month commitment wise when monthly spend varies 40 percent? Answer in at most 80 words."],
 "summary": ["Summarise in one sentence: 'The support team reviewed 1,200 tickets in March, found that 18 percent were duplicates, merged them, and cut the time to first reply by a third after changing the routing rule.'", "Summarise in one sentence: 'Fieldstone moved nightly enrichment to a batch interface, kept a synchronous fallback, and saw spend on the job fall by half while results arrived by 05:00.'"],
}
def one(a):
    cl, m, kind, pi, rep = a
    x = cl.messages.create(model=m, max_tokens=4000, messages=[{"role": "user", "content": P[kind][pi]}])
    text = "".join(b.text for b in x.content if b.type == "text")
    return {"model": m, "kind": kind, "p": pi, "rep": rep, "in": x.usage.input_tokens, "out": x.usage.output_tokens, "text_chars": len(text), "types": [b.type for b in x.content], "stop": x.stop_reason}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, k, i, r) for m in MODELS for k in P for i in range(2) for r in range(3)]
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(one, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
    for k in P:
        row = [k]
        for m in MODELS:
            q = [x for x in res if x["model"] == m and x["kind"] == k]
            row.append("%s out %.0f chars %.0f thinking %d/%d" % (m[7:16], sum(x["out"] for x in q)/len(q), sum(x["text_chars"] for x in q)/len(q), sum("thinking" in x["types"] for x in q), len(q)))
        print(" | ".join(row))
    for m in MODELS:
        q = [x for x in res if x["model"] == m]; print(m, "mean out %.0f" % (sum(x["out"] for x in q)/len(q)), "mean in %.0f" % (sum(x["in"] for x in q)/len(q)), "stops", sorted({x["stop"] for x in q}))
if __name__ == "__main__": main()
