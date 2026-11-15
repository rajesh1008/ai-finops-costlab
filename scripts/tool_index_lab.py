#!/usr/bin/env python3
"""Ch19 lab (50th run, EnvOpt idea). REAL calls. Return all ten search results in full, or an index first and the one document the model picks?
Arm full: ten ~450-word documents in one prompt, question, answer. Arm index: ten one-line summaries, model names the document number,
then that document alone goes in a second call. 20 questions per arm; each document holds one numeric fact; scored by exact number.
Model claude-haiku-4-5-20251001. Key from env only, never printed."""
import os, sys, json, random, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
M = "claude-haiku-4-5-20251001"; PIN, POUT = 1.00, 5.00
OUT = Path(__file__).resolve().parents[1] / "runs" / "tool-index-lab-2026-11-15.jsonl"
TOPICS = "refund limits|invoice disputes|seat transfers|data export|api rate caps|sso setup|audit logs|trial extensions|tax exemptions|storage tiers".split("|")
FILL = "The team reviewed the process, noted the exceptions raised by regional staff, and recorded the agreed wording for the help centre. Reviewers asked for plain examples and a short list of edge cases. ".split()
def corpus(seed):
    rng = random.Random(seed); docs = []
    for i, t in enumerate(TOPICS):
        n = rng.randint(11, 98); body = " ".join(rng.choice(["Note", "Policy", "Detail"]) + f" {j}: " + " ".join(FILL[: rng.randint(18, 30)]) for j in range(1, 12))
        docs.append({"id": i + 1, "topic": t, "n": n, "text": f"Document {i+1} on {t}. {body} The limit for {t} on the standard plan is {n} units. {body[::-1][:0]}"})
    return docs
def call(cl, prompt, mt=12):
    r = cl.messages.create(model=M, max_tokens=mt, messages=[{"role": "user", "content": prompt}])
    return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
def cost(i, o): return (i * PIN + o * POUT) / 1e6
def trial(cl, q):
    docs = corpus(q); rng = random.Random(q * 7); d = rng.choice(docs)
    question = f"What is the limit for {d['topic']} on the standard plan? Answer with the number only."
    full = "\n\n".join(x["text"] for x in docs)
    a, i1, o1 = call(cl, f"Search results:\n\n{full}\n\n{question}")
    idx = "\n".join(f"{x['id']}. {x['topic']}" for x in docs)
    p, i2, o2 = call(cl, f"Search index:\n{idx}\n\n{question}\nWhich document number would you open? Answer with the number only.", 40)
    m = re.search(r"\d+", p); pick = int(m.group()) if m else 0
    doc = next((x for x in docs if x["id"] == pick), docs[0])
    b, i3, o3 = call(cl, f"Document:\n{doc['text']}\n\n{question}")
    return {"q": q, "truth": d["n"], "full": {"ans": a, "ok": re.sub(r"\D", "", a) == str(d["n"]), "in": i1, "out": o1, "cost": cost(i1, o1)},
            "index": {"raw_pick": p, "pick": pick, "right_pick": pick == d["id"], "ans": b, "ok": re.sub(r"\D", "", b) == str(d["n"]), "in": i2 + i3, "out": o2 + o3, "cost": cost(i2 + i3, o2 + o3)}}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic()
    with ThreadPoolExecutor(4) as ex: rows = list(ex.map(lambda q: trial(cl, q), range(20)))
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
def summarise(rows):
    n = len(rows)
    return {"n": n, "full_ok": sum(r["full"]["ok"] for r in rows), "index_ok": sum(r["index"]["ok"] for r in rows),
            "right_pick": sum(r["index"]["right_pick"] for r in rows),
            "full_cost": sum(r["full"]["cost"] for r in rows) / n, "index_cost": sum(r["index"]["cost"] for r in rows) / n,
            "full_in": sum(r["full"]["in"] for r in rows) / n, "index_in": sum(r["index"]["in"] for r in rows) / n}
def summary(path=OUT):
    s = summarise([json.loads(l) for l in Path(path).read_text().splitlines()]); print(s); print("cost ratio index/full", s["index_cost"] / s["full_cost"])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
