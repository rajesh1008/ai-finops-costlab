#!/usr/bin/env python3
"""Ch23 lab (38th run). REAL calls. Does the position of the one useful passage in a 12-passage context change accuracy? That decides whether a reranker (which moves the best passage first) is worth paying for.
10 questions x 3 gold positions (1, 6, 12) x 2 models = 60 calls. Passages are invented near-duplicate clauses about 12 plans; the question names one plan. Full replies stored. Key from env only."""
import os, sys, json, random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
PLANS = ["Alder", "Birch", "Cedar", "Dogwood", "Elm", "Fir", "Ginkgo", "Hazel", "Iroko", "Juniper", "Kauri", "Larch"]
rng = random.Random(38)
FACT = {p: {"days": rng.choice(range(7, 61)), "seats": rng.choice(range(5, 400)), "fee": rng.choice(range(11, 990))} for p in PLANS}
def passage(p):
    f = FACT[p]
    return (f"Plan {p}: customers may request a refund within {f['days']} days of purchase. The plan includes {f['seats']} seats. "
            f"The monthly platform fee is {f['fee']} dollars. Overage seats are billed at the list rate.")
QS = []
for i, p in enumerate(PLANS[:10]):
    kind = ["days", "seats", "fee"][i % 3]
    q = {"days": f"How many days does a customer on plan {p} have to request a refund?", "seats": f"How many seats are included in plan {p}?", "fee": f"What is the monthly platform fee for plan {p}, in dollars?"}[kind]
    QS.append((p, kind, q, str(FACT[p][kind])))
OUT = Path(__file__).resolve().parents[1] / "runs" / "gold-position-lab-2026-11-13.jsonl"
def build(p, pos):
    others = [x for x in PLANS if x != p]; random.Random(sum(map(ord, p)) + pos).shuffle(others)
    order = others[:pos - 1] + [p] + others[pos - 1:11]
    return "\n\n".join(passage(x) for x in order)
def one(a):
    cl, qi, pos, mi = a
    p, kind, q, ans = QS[qi]
    prompt = "Answer using only the passages below. Reply with the number only.\n\n" + build(p, pos) + "\n\nQuestion: " + q
    x = cl.messages.create(model=MODELS[mi], max_tokens=60, messages=[{"role": "user", "content": prompt}])
    r = "".join(b.text for b in x.content if b.type == "text").strip()
    digits = "".join(c for c in r if c.isdigit())
    return {"q": qi, "pos": pos, "model": MODELS[mi], "input": x.usage.input_tokens, "out": x.usage.output_tokens, "answer": ans, "reply": r, "ok": digits == ans}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    cl = Anthropic(); jobs = [(cl, qi, pos, mi) for qi in range(10) for pos in (1, 6, 12) for mi in (0, 1)]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"q": j[1], "pos": j[2], "model": MODELS[j[3]], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(6) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]; good = [r for r in rows if "error" not in r]
    print("calls", len(rows), "errors", len(rows) - len(good))
    for m in MODELS:
        for pos in (1, 6, 12):
            rs = [r for r in good if r["model"] == m and r["pos"] == pos]
            if rs: print(m, "pos", pos, "n", len(rs), "correct", sum(r["ok"] for r in rs), "mean_in", round(sum(r["input"] for r in rs) / len(rs), 1))
    print("wrong:", [(r["model"][-6:], r["pos"], r["q"], r["reply"][:30], r["answer"]) for r in good if not r["ok"]])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
