"""Chapters 27-29: shared pieces for the degradation-ladder, shadow-mode and judge-cost labs.
SYNTHETIC Fieldstone handbook (160 clauses, same generator as the Chapter 24-26 labs), question templates, a deterministic (no-model) rung, an exact-match cache,
a pace-based ladder controller, a scorer, and the small statistics the three chapters use (Wilson interval, paired difference, prediction-powered estimate).
Everything here is deterministic given a seed; model calls live in scripts/."""
import math, random, re
from collections import OrderedDict

def nxt(i): return (i * 37 + 11) % 160 + 1
def ref(i): return f"FS-{1000 + i * 13}"
def days(i): return 30 + (i % 12) * 15

def clauses(edited=()):
    """160 clauses. `edited` is a set of clause numbers whose retention window is 15 days longer (a handbook revision)."""
    out = []
    for i in range(1, 161):
        d = days(i) + (15 if i in edited else 0)
        out.append({"i": i, "ref": ref(i), "days": d,
                    "text": f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account owner, record reference {ref(i)}, and confirm the retention window of {d} days before describing any export or deletion procedure. If unresolved, escalate per clause {nxt(i)}."})
    return out

def make_questions(n, seed, mix=(0.4, 0.3, 0.3)):
    """Templates: A reference and window for clause i; B window for the clause carrying a reference code; C reference and window of the clause that clause i escalates to (two lookups)."""
    rnd = random.Random(seed); qs = []
    for k in range(n):
        i = rnd.randint(1, 160); u = rnd.random()
        if u < mix[0]: qs.append({"t": "A", "clause": i, "q": f"What is the FS reference code and the retention window in days for clause {i}?", "gold": [ref(i), str(days(i))], "needs": [i]})
        elif u < mix[0] + mix[1]: qs.append({"t": "B", "clause": i, "q": f"A support agent must record reference {ref(i)}. How many days is the retention window for that clause?", "gold": [str(days(i))], "needs": [i]})
        else:
            j = nxt(i); qs.append({"t": "C", "clause": i, "q": f"Start at clause {i} of the handbook. Follow its escalation instruction once (go to the clause it names). Report the FS reference code and the retention window in days of the clause you end on.", "gold": [ref(j), str(days(j))], "needs": [j]})
    return qs

def score(answer, gold):
    """True if the answer text contains every gold token (reference codes as written, day counts as whole numbers)."""
    if not answer: return False
    for g in gold:
        if g.startswith("FS-"):
            if not re.search(rf"(?<![\w-]){re.escape(g)}(?!\d)", answer): return False
        elif not re.search(rf"(?<![\d-]){re.escape(g)}(?![\d])", answer): return False
    return True

def deterministic_answer(question, bm, C):
    """The no-model rung: regex intent plus BM25 lookup. Answers templates A and B. Returns None (abstains) for anything it cannot parse, including every escalation question."""
    ql = question.lower()
    if "escalat" in ql: return None
    m = re.search(r"clause (\d+)", ql)
    if m and "reference code and the retention window" in ql:
        i = int(m.group(1)); top = bm.search(f"Clause {i}.", 3)
        for t in top:
            if C[t]["i"] == i: return f"{C[t]['ref']}; {C[t]['days']} days"
        return None
    m = re.search(r"(FS-\d+)", question)
    if m and "retention window" in ql:
        top = bm.search(m.group(1), 3)
        for t in top:
            if C[t]["ref"] == m.group(1): return f"{C[t]['days']} days"
    return None

class ExactCache:
    """Exact-match cache on a normalised question key with an optional entry limit (LRU)."""
    def __init__(self, limit=None): self.d = OrderedDict(); self.limit = limit; self.hits = 0; self.misses = 0
    @staticmethod
    def key(q): return re.sub(r"\s+", " ", q.lower().strip().rstrip("?."))
    def get(self, q):
        k = self.key(q)
        if k in self.d: self.d.move_to_end(k); self.hits += 1; return self.d[k]
        self.misses += 1; return None
    def put(self, q, a):
        k = self.key(q); self.d[k] = a; self.d.move_to_end(k)
        if self.limit and len(self.d) > self.limit: self.d.popitem(last=False)

def zipf_stream(n_req, n_items, s, seed):
    rnd = random.Random(seed); w = [1 / (r + 1) ** s for r in range(n_items)]; order = list(range(n_items)); rnd.shuffle(order)
    return [order[i] for i in rnd.choices(range(n_items), weights=w, k=n_req)]

RUNGS = ("cache", "full", "reduced", "deterministic", "off")

def run_ladder(stream, table, budget, policy, cost_mean, cache_limit=None):
    """Replay a request stream against a daily budget (dollars).
    table[q] = {rung: (cost, correct_or_None)} for rungs full, reduced, deterministic (None = abstained or an explicit decline, counted as 'off', not as wrong). Cached answers carry the correctness and staleness recorded in table[q]['stale'] (True means the cached copy is out of date).
    policy: 'cliff' (full until the budget is gone, then off), 'cliff_cache' (cache first, then as cliff), 'ladder' (cache first, then the best rung the per-request allowance can pay for after allowing for the observed hit rate, then deterministic, then off), 'ladder_naive' (same, pacing as if there were no cache), 'ladder_prior' (same, pacing with a miss share supplied in advance as cost_mean['_miss'], for example yesterday's).
    Returns spend, correct, wrong, off counts."""
    cache = ExactCache(cache_limit); left = budget; n = len(stream); seen = 0; miss = 0; out = {"spend": 0.0, "correct": 0, "wrong": 0, "off": 0, "off_last_fifth": 0, "by_rung": {r: 0 for r in RUNGS}}
    for k, q in enumerate(stream):
        remaining = n - k; allow = left / remaining if remaining else 0
        t = table[q]
        if policy in ("cliff_cache", "ladder", "ladder_naive", "ladder_prior"):
            c = cache.get(t["key"])
            if c is not None:
                seen += 1; out["by_rung"]["cache"] += 1
                if c[0] is None: out["off"] += 1; out["off_last_fifth"] += int(k >= 0.8 * n)
                else: out["correct" if (c[0] and not t["stale"]) else "wrong"] += 1
                continue
        seen += 1; miss += 1
        # 'ladder' prices each rung at its mean cost times the miss share seen so far (a cache hit costs nothing); 'ladder_naive' ignores the cache when it paces.
        m = (miss / seen) if (policy == "ladder" and seen >= 20) else (cost_mean.get("_miss", 1.0) if policy == "ladder_prior" else 1.0)
        rung = None
        if policy in ("cliff", "cliff_cache"): rung = "full" if left >= t["full"][0] else None
        else:
            if allow >= m * cost_mean["full"] and left >= t["full"][0]: rung = "full"
            elif allow >= m * cost_mean["reduced"] and left >= t["reduced"][0]: rung = "reduced"
            elif t["deterministic"][1] is not None: rung = "deterministic"
        if rung is None: out["off"] += 1; out["off_last_fifth"] += int(k >= 0.8 * n); out["by_rung"]["off"] += 1; continue
        cost, ok = t[rung]; left -= cost; out["spend"] += cost; out["by_rung"][rung] += 1
        if ok is None: out["off"] += 1; out["off_last_fifth"] += int(k >= 0.8 * n)   # an explicit decline: the user is told no answer, which is not a confident wrong answer
        else: out["correct" if ok else "wrong"] += 1
        if policy in ("cliff_cache", "ladder", "ladder_naive", "ladder_prior"): cache.put(t["key"], (ok,))
    return out

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

def paired_diff(a, b):
    """a, b: lists of 0/1 for the same items. Returns (mean b-a, standard error, b-only wins, a-only wins)."""
    d = [y - x for x, y in zip(a, b)]; n = len(d); m = sum(d) / n
    var = sum((x - m) ** 2 for x in d) / (n - 1) if n > 1 else 0.0
    return m, math.sqrt(var / n), sum(1 for x, y in zip(a, b) if y and not x), sum(1 for x, y in zip(a, b) if x and not y)

def ppi_mean(judge_unlab, judge_cal, gold_cal):
    """Prediction-powered estimate of the mean of a 0/1 gold label: judge mean on the large unlabelled set, corrected by the average judge error on a small gold-labelled set. Returns (estimate, standard error)."""
    n, m = len(judge_unlab), len(judge_cal); p = sum(judge_unlab) / n
    resid = [j - g for j, g in zip(judge_cal, gold_cal)]; rm = sum(resid) / m
    pv = p * (1 - p) / n; rv = sum((r - rm) ** 2 for r in resid) / (m - 1) / m if m > 1 else 0.0
    return p - rm, math.sqrt(pv + rv)

def normal_ci(est, se, z=1.96): return est - z * se, est + z * se

def usd(inp, out, rates): return inp / 1e6 * rates[0] + out / 1e6 * rates[1]
