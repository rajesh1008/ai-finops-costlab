#!/usr/bin/env python3
"""Chapter 25 lab (twenty-first run). REAL calls. Same job done by one call (S) or by a planner-free fan-out of six workers plus a merge call (F).
Job: six synthetic service reports each hold one approved refund amount plus a requested and a prior amount; report the six approved amounts and their total.
Documents, amounts and the shared brief are mine. Never prints the key."""
import os, sys, json, random, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
MERGE_MAX = int(os.environ.get("MERGE_MAX", "30")); WORK_MAX = int(os.environ.get("WORK_MAX", "40"))
OUT = Path(__file__).resolve().parents[1] / "runs" / f"fanout-lab-2026-11-11-w{WORK_MAX}-m{MERGE_MAX}.jsonl"
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
REPS = int(os.environ.get("REPS", "10"))
FILL = ["The customer wrote in about a delayed delivery and the agent checked the order history.", "A supervisor reviewed the case notes and asked for the courier record.", "The warehouse confirmed the parcel left on the stated day and was held at a depot.", "The customer asked twice for an update and was given a new estimate each time.", "The agent apologised and explained the steps that would follow."]
BRIEF = ("You are one worker in a refund review team. Read the single report you are given. Reports contain a requested amount, a prior credit already paid and an approved amount. "
 "Only the approved amount counts. Ignore requested and prior figures. Reply with the approved amount as digits only. ") * 3
def make(rep):
    r = random.Random(2500 + rep); docs = []
    for i in range(6):
        ap, rq, pr = r.randint(20, 400), r.randint(20, 400), r.randint(5, 90)
        body = [r.choice(FILL) for _ in range(14)]
        body.insert(r.randint(2, 12), f"The customer requested a refund of {rq} dollars.")
        body.insert(r.randint(2, 12), f"A prior credit of {pr} dollars was paid on the first complaint.")
        body.insert(r.randint(2, 12), f"After review the approved refund is {ap} dollars.")
        docs.append((ap, f"Report {i+1}\n" + " ".join(body)))
    return docs
def call(cl, m, prompt, mx=300):
    x = cl.messages.create(model=m, max_tokens=mx, messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in x.content if b.type == "text"), x.usage.input_tokens, x.usage.output_tokens
def nums(t): return [int(v) for v in re.findall(r"\d+", t)]
def one(args):
    cl, m, rep = args; docs = make(rep); truth = [d[0] for d in docs]; rec = []
    t, i, o = call(cl, m, "Below are six reports. Each has one approved refund amount (ignore requested and prior figures). Reply with only the six approved amounts, comma separated, then a final line TOTAL: and the sum.\n\n" + "\n\n".join(d[1] for d in docs))
    got = nums(t); ok = got[:6] == truth and got[-1:] == [sum(truth)]
    rec.append({"cond": "S", "model": m, "rep": rep, "in": i, "out": o, "calls": 1, "ok": ok, "docs_ok": sum(a == b for a, b in zip(got[:6], truth))})
    wi = wo = 0; outs = []; empty = 0
    for a, d in docs:
        t, i, o = call(cl, m, BRIEF + "\n\n" + d, WORK_MAX); wi += i; wo += o; n = nums(t); empty += (not t.strip()); outs.append(n[0] if n else -1)
    t, i, o = call(cl, m, "Six workers each reported one approved amount: " + ", ".join(map(str, outs)) + ". Reply with only the total as digits.", MERGE_MAX); wi += i; wo += o
    tot = nums(t); mempty = not t.strip(); ok = outs == truth and tot[:1] == [sum(truth)]
    rec.append({"cond": "F", "model": m, "rep": rep, "in": wi, "out": wo, "calls": 7, "ok": ok, "docs_ok": sum(a == b for a, b in zip(outs, truth)), "empty_worker_texts": empty, "empty_merge": mempty})
    return rec
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, m, r) for m in MODELS for r in range(REPS)]
    with ThreadPoolExecutor(6) as ex: res = [x for g in ex.map(one, jobs) for x in g]
    OUT.write_text("\n".join(json.dumps(x) for x in res) + "\n")
    for m in MODELS:
        for c in "SF":
            q = [x for x in res if x["model"] == m and x["cond"] == c]
            print(m, c, "n", len(q), "all-correct", sum(x["ok"] for x in q), "docs_ok mean %.2f" % (sum(x["docs_ok"] for x in q)/len(q)), "in/run %.0f out/run %.0f calls %d" % (sum(x["in"] for x in q)/len(q), sum(x["out"] for x in q)/len(q), q[0]["calls"]))
if __name__ == "__main__": main()
