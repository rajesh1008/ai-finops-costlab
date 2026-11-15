"""Chapter 17: routing and cascade policies evaluated over recorded real answers. Problems are SYNTHETIC with exact answers."""
import random, re

def make_problems(n=30, seed=17):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        s = rnd.randint(8, 30); p = rnd.choice([29, 39, 45, 49, 59, 79]); d = rnd.choice([5, 10, 12, 15, 20, 25])
        r = rnd.randint(2, max(2, s // 3))
        ans = round((s - r) * p * (1 - d / 100), 2)
        q = (f"A customer was charged ${p} per seat for {s} seats, then given a {d} percent discount on the total, "
             f"then refunded for {r} seats at the discounted per-seat price. What is the net amount charged? "
             "Give the number and one sentence.")
        out.append({"id": i, "q": q, "answer": ans})
    return out

def numbers(text):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))]

def correct(text, ans):
    """Loose check: some number in the reply equals the exact answer to the cent."""
    return any(abs(x - ans) < 0.005 for x in numbers(text))

def final_number(text):
    """The stated answer: the first bold dollar amount if the reply has one, else the first dollar amount, else the first number.
    A production cascade has no answer key, so agreement has to be read off the replies like this."""
    t = text.replace(",", "")
    m = re.findall(r"\*\*\$\s?(\d+(?:\.\d+)?)\*\*", t) or re.findall(r"\$\s?(\d+(?:\.\d+)?)", t)
    if m: return float(m[0])
    n = numbers(text)
    return n[0] if n else None

def agree(a, b):
    x, y = final_number(a), final_number(b)
    return x is not None and y is not None and abs(x - y) < 0.005
