#!/usr/bin/env python3
"""Ch23 lab (40th run). REAL calls. Does a model-based reranker pay for itself? 12 invented near-duplicate plan passages (as gold_position_lab). 20 questions x 2 models.
Condition direct: all 12 passages + question -> answer. Condition rerank: call 1 shows the 12 numbered passages and asks for the ids of the 2 most useful (short output); call 2 answers from only those 2.
Per question 3 calls (token cap 400 on every call; a first run with a cap of 20 on the rerank call truncated haiku-5-5 thinking and is kept as runs/llm-rerank-lab-2026-11-13-cap20-truncated.jsonl) per model = 120 calls. Gold passage placed at position 1, 6 or 12 by question index. Full replies stored. Key from env only."""
import os, sys, json, random, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
MODELS = ["claude-haiku-4-5-20251001", "claude-haiku-5-5"]
PLANS = ["Alder", "Birch", "Cedar", "Dogwood", "Elm", "Fir", "Ginkgo", "Hazel", "Iroko", "Juniper", "Kauri", "Larch"]
rng = random.Random(40)
FACT = {p: {"days": rng.choice(range(7, 61)), "seats": rng.choice(range(5, 400)), "fee": rng.choice(range(11, 990))} for p in PLANS}
def passage(p):
    f = FACT[p]
    return (f"Plan {p}: customers may request a refund within {f['days']} days of purchase. The plan includes {f['seats']} seats. "
            f"The monthly platform fee is {f['fee']} dollars. Overage seats are billed at the list rate.")
QS = []
for i in range(20):
    p = PLANS[i % 12]; kind = ["days", "seats", "fee"][i % 3]
    q = {"days": f"How many days does a customer on plan {p} have to request a refund?", "seats": f"How many seats are included in plan {p}?", "fee": f"What is the monthly platform fee for plan {p}, in dollars?"}[kind]
    QS.append((p, kind, q, str(FACT[p][kind]), (1, 6, 12)[i % 3]))
OUT = Path(__file__).resolve().parents[1] / "runs" / "llm-rerank-lab-2026-11-13.jsonl"
def order(p, pos, i):
    others = [x for x in PLANS if x != p]; random.Random(i * 7 + pos).shuffle(others)
    return others[:pos - 1] + [p] + others[pos - 1:11]
def txt(x): return "".join(b.text for b in x.content if b.type == "text").strip()
def num(r): return "".join(c for c in r if c.isdigit())
def one(a):
    cl, qi, mi = a
    p, kind, q, ans, pos = QS[qi]; m = MODELS[mi]; od = order(p, pos, qi)
    allp = "\n\n".join(f"[{j+1}] {passage(x)}" for j, x in enumerate(od))
    d = cl.messages.create(model=m, max_tokens=400, messages=[{"role": "user", "content": "Answer using only the passages below. Reply with the number only.\n\n" + allp + "\n\nQuestion: " + q}])
    rr = cl.messages.create(model=m, max_tokens=400, messages=[{"role": "user", "content": "Below are numbered passages and a question. Reply with only the numbers of the two passages most useful for answering, separated by a comma.\n\n" + allp + "\n\nQuestion: " + q}])
    ids = [int(x) for x in re.findall(r"\d+", txt(rr))][:2]
    keep = [od[j - 1] for j in ids if 1 <= j <= len(od)]
    sub = "\n\n".join(passage(x) for x in keep)
    a2 = cl.messages.create(model=m, max_tokens=400, messages=[{"role": "user", "content": "Answer using only the passages below. Reply with the number only.\n\n" + sub + "\n\nQuestion: " + q}])
    return {"q": qi, "pos": pos, "model": m, "answer": ans, "gold_kept": p in keep,
            "direct": {"in": d.usage.input_tokens, "out": d.usage.output_tokens, "reply": txt(d), "ok": num(txt(d)) == ans},
            "rerank": {"in": rr.usage.input_tokens, "out": rr.usage.output_tokens, "reply": txt(rr)},
            "final": {"in": a2.usage.input_tokens, "out": a2.usage.output_tokens, "reply": txt(a2), "ok": num(txt(a2)) == ans}}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic(); jobs = [(cl, qi, mi) for qi in range(20) for mi in (0, 1)]
    def safe(j):
        try: return one(j)
        except Exception as e: return {"q": j[1], "model": MODELS[j[2]], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(4) as ex: rows = list(ex.map(safe, jobs))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
PRICE = {MODELS[0]: (1.0, 5.0), MODELS[1]: (0.10, 0.50)}
def summary():
    rows = [json.loads(l) for l in OUT.read_text().splitlines()]; good = [r for r in rows if "error" not in r]
    print("rows", len(rows), "errors", len(rows) - len(good), "calls", 3 * len(good))
    for m in MODELS:
        rs = [r for r in good if r["model"] == m]; pi, po = PRICE[m]
        c = lambda *parts: sum(x["in"] * pi + x["out"] * po for r in rs for x in [r[k] for k in parts]) / 1e6 / len(rs) * 1000
        print(m, "n", len(rs), "direct ok", sum(r["direct"]["ok"] for r in rs), "rerank-path ok", sum(r["final"]["ok"] for r in rs), "gold kept", sum(r["gold_kept"] for r in rs))
        print("  mean in direct", round(sum(r["direct"]["in"] for r in rs) / len(rs), 1), "rerank call in", round(sum(r["rerank"]["in"] for r in rs) / len(rs), 1), "final in", round(sum(r["final"]["in"] for r in rs) / len(rs), 1))
        print("  $/1000 direct", round(c("direct"), 4), "rerank path (2 calls)", round(c("rerank", "final"), 4), "answer step alone", round(c("final"), 4))
        for pos in (1, 6, 12):
            q = [r for r in rs if r["pos"] == pos]; print("  pos", pos, "n", len(q), "direct", sum(r["direct"]["ok"] for r in q), "path", sum(r["final"]["ok"] for r in q), "kept", sum(r["gold_kept"] for r in q))
    print("misses:", [(r["model"][-6:], r["pos"], r["q"], r["rerank"]["reply"][:15], r["final"]["reply"][:20], r["direct"]["reply"][:20]) for r in good if not (r["direct"]["ok"] and r["final"]["ok"])])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
