"""Chapter 47: extract (question, strong answer, weak answer) triples from the book's own Interview Questions and Answers sections, and score pairwise grading with position and length controls."""
import re, glob, random
def extract(manuscript_glob):
    out = []
    for f in sorted(glob.glob(manuscript_glob)):
        t = open(f).read()
        if "## Interview Questions" not in t: continue
        sec = t.split("## Interview Questions", 1)[1]
        for p in re.split(r"\n### ", sec)[1:]:
            q, _, rest = p.partition("\n")
            m = re.search(r"\nA weak answer: (.*?)(?:\n|$)", rest)
            if not m: continue
            strong = rest[:m.start()].strip(); weak = m.group(1).strip().strip('"').strip("\u201c\u201d").strip()
            if len(strong) > 40 and weak: out.append({"file": f.split("/")[-1][:4], "q": q.strip(), "strong": strong, "weak": weak})
    return out
def sample(triples, n, seed=11): return random.Random(seed).sample(triples, n)
def first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text, re.S); return m.group(1) if m else text
def pick_strong_rate(rows): return sum(1 for r in rows if r["picked"] == "strong") / len(rows)
def position_bias(rows):
    """share of picks that were option A, over all rows (0.5 is no bias when strong sits in A half the time)."""
    return sum(1 for r in rows if r["choice"] == "A") / len(rows)

# --- offline heuristic graders (no model). Each returns True when it prefers the strong answer. ---
import re as _re
def words(t): return _re.findall(r"[A-Za-z0-9$%.']+", t)
def h_longer(strong, weak, q): return len(words(strong)) > len(words(weak))
def h_numbers(strong, weak, q): return len(_re.findall(r"\d", strong)) > len(_re.findall(r"\d", weak))
def h_overlap(strong, weak, q):
    qs = {w.lower() for w in words(q) if len(w) > 3}
    f = lambda t: len({w.lower() for w in words(t)} & qs) / max(1, len(words(t)))
    return f(strong) > f(weak)
def h_hedges(strong, weak, q):
    """prefers the answer with more conditional or limiting words (if, but, unless, because, only, first, then)."""
    k = {"if", "but", "unless", "because", "only", "first", "then", "when", "until", "except"}
    c = lambda t: sum(1 for w in words(t) if w.lower() in k)
    return c(strong) > c(weak)
HEUR = {"longer": h_longer, "more digits": h_numbers, "overlap with question": h_overlap, "conditional words": h_hedges}
