#!/usr/bin/env python3
"""Ch23 lab (41st run). REAL calls. Cheap selector + dearer answerer. 40 invented near-duplicate plan passages, 20 questions.
Path A (baseline): answerer model reads all 40 passages. Path B: selector model (cheap) reads all 40 and returns the ids of the 2 most useful;
answerer model reads only those 2. 3 calls per question (A, selector, answerer) = 60 calls. Gold at position 1, 20 or 40. Token cap 600 on every call.
Selector = claude-haiku-5-5 (lower list price, reasons before answering); answerer = claude-haiku-4-5-20251001. Key from env only; full replies stored."""
import os, sys, json, random, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
SEL, ANS = "claude-haiku-5-5", "claude-haiku-4-5-20251001"
PRICE = {SEL: (0.10, 0.50), ANS: (1.0, 5.0)}
NAMES = ["Alder","Birch","Cedar","Dogwood","Elm","Fir","Ginkgo","Hazel","Iroko","Juniper","Kauri","Larch","Maple","Nutmeg","Olive","Pine","Quince","Rowan","Spruce","Tamarack","Umbrella","Vine","Willow","Yew","Zelkova","Acacia","Banyan","Cypress","Date","Ebony","Fig","Gum","Holly","Ironwood","Jarrah","Kapok","Linden","Mulberry","Neem","Oak"]
rng = random.Random(41)
FACT = {p: {"days": rng.choice(range(7, 61)), "seats": rng.choice(range(5, 400)), "fee": rng.choice(range(11, 990))} for p in NAMES}
def passage(p):
    f = FACT[p]
    return (f"Plan {p}: customers may request a refund within {f['days']} days of purchase. The plan includes {f['seats']} seats. "
            f"The monthly platform fee is {f['fee']} dollars. Overage seats are billed at the list rate.")
QS = []
for i in range(20):
    p = NAMES[(i * 2 + 1) % 40]; kind = ["days", "seats", "fee"][i % 3]
    q = {"days": f"How many days does a customer on plan {p} have to request a refund?", "seats": f"How many seats are included in plan {p}?", "fee": f"What is the monthly platform fee for plan {p}, in dollars?"}[kind]
    QS.append((p, kind, q, str(FACT[p][kind]), (1, 20, 40)[i % 3]))
OUT = Path(__file__).resolve().parents[1] / "runs" / "selector-answerer-lab-2026-11-13.jsonl"
def order(p, pos, i):
    others = [x for x in NAMES if x != p]; random.Random(i * 11 + pos).shuffle(others)
    return others[:pos - 1] + [p] + others[pos - 1:39]
def txt(x): return "".join(b.text for b in x.content if b.type == "text").strip()
def num(r): return "".join(c for c in r if c.isdigit())
def call(cl, m, prompt):
    r = cl.messages.create(model=m, max_tokens=600, messages=[{"role": "user", "content": prompt}])
    return r, {"in": r.usage.input_tokens, "out": r.usage.output_tokens, "reply": txt(r), "stop": r.stop_reason}
def one(a):
    cl, qi = a
    p, kind, q, ans, pos = QS[qi]; od = order(p, pos, qi)
    allp = "\n\n".join(f"[{j+1}] {passage(x)}" for j, x in enumerate(od))
    _, A = call(cl, ANS, "Answer using only the passages below. Reply with the number only.\n\n" + allp + "\n\nQuestion: " + q)
    A["ok"] = num(A["reply"]) == ans
    _, S = call(cl, SEL, "Below are numbered passages and a question. Reply with only the numbers of the two passages most useful for answering, separated by a comma.\n\n" + allp + "\n\nQuestion: " + q)
    ids = [int(x) for x in re.findall(r"\d+", S["reply"])][:2]
    keep = [od[j - 1] for j in ids if 1 <= j <= len(od)]
    sub = "\n\n".join(passage(x) for x in keep)
    _, F = call(cl, ANS, "Answer using only the passages below. Reply with the number only.\n\n" + sub + "\n\nQuestion: " + q)
    F["ok"] = num(F["reply"]) == ans
    return {"q": qi, "pos": pos, "answer": ans, "gold_kept": p in keep, "direct": A, "select": S, "final": F}
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"): sys.exit("ANTHROPIC_API_KEY is not set")
    from anthropic import Anthropic
    cl = Anthropic()
    def safe(j):
        try: return one(j)
        except Exception as e: return {"q": j[1], "error": type(e).__name__ + ": " + str(e)[:160]}
    with ThreadPoolExecutor(4) as ex: rows = list(ex.map(safe, [(cl, qi) for qi in range(20)]))
    OUT.write_text("\n".join(json.dumps(x) for x in rows) + "\n")
def cost(rows, parts):
    t = 0.0
    for r in rows:
        for k, m in parts:
            pi, po = PRICE[m]; t += r[k]["in"] * pi + r[k]["out"] * po
    return t / 1e6 / len(rows) * 1000
def summary(path=OUT):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines()]; good = [r for r in rows if "error" not in r]
    print("rows", len(rows), "errors", len(rows) - len(good), "calls", 3 * len(good))
    print("direct (answerer on 40) ok", sum(r["direct"]["ok"] for r in good), "pair path ok", sum(r["final"]["ok"] for r in good), "gold kept", sum(r["gold_kept"] for r in good))
    print("mean in: direct", round(sum(r["direct"]["in"] for r in good) / len(good), 1), "select", round(sum(r["select"]["in"] for r in good) / len(good), 1), "final", round(sum(r["final"]["in"] for r in good) / len(good), 1))
    print("mean out: select", round(sum(r["select"]["out"] for r in good) / len(good), 1), "truncated selects", sum(r["select"]["stop"] == "max_tokens" for r in good))
    d = cost(good, [("direct", ANS)]); s = cost(good, [("select", SEL)]); f = cost(good, [("final", ANS)])
    print("$/1000: direct", round(d, 4), "selector", round(s, 4), "final answer", round(f, 4), "pair path", round(s + f, 4), "ratio", round((s + f) / d, 3))
    for pos in (1, 20, 40):
        q = [r for r in good if r["pos"] == pos]; print("pos", pos, "n", len(q), "direct", sum(r["direct"]["ok"] for r in q), "path", sum(r["final"]["ok"] for r in q), "kept", sum(r["gold_kept"] for r in q))
    print("misses:", [(r["pos"], r["q"], r["select"]["reply"][:15], r["final"]["reply"][:20], r["direct"]["reply"][:20]) for r in good if not (r["direct"]["ok"] and r["final"]["ok"])])
if __name__ == "__main__":
    summary() if len(sys.argv) > 1 and sys.argv[1] == "summary" else main()
