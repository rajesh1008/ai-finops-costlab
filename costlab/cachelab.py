"""Chapter 18: prompt-cache arithmetic, a toy semantic cache, and a cache-health check. Inputs SYNTHETIC or ASSUMED, labelled in the text."""
import math, random, re
from collections import Counter

# multipliers from the vendor page (opened 10 Nov 2026): 5-minute write 1.25x, 1-hour write 2x, read 0.1x (most models)
W5, W1H, READ = 1.25, 2.0, 0.10

def call_cost(prefix_tokens, suffix_tokens, price_in, mode):
    """USD for one call. mode: 'none', 'write5', 'write1h', 'read'."""
    m = 1e6
    suffix = suffix_tokens * price_in / m
    if mode == "none": return (prefix_tokens + suffix_tokens) * price_in / m
    mult = {"write5": W5, "write1h": W1H, "read": READ}[mode]
    return prefix_tokens * price_in * mult / m + suffix

def breakeven_reads(write_mult):
    """Smallest number of later reads at which writing beats never caching (suffix ignored):
    write_mult + n*READ < (1+n)  ->  n > (write_mult-1)/(1-READ)."""
    return math.floor((write_mult - 1) / (1 - READ)) + 1

def session_cost(gaps_min, prefix, suffix, price_in, ttl_min=5, write_mult=W5):
    """Cost of a series of calls separated by gaps (minutes). A read refreshes the entry; a gap above ttl evicts it."""
    total = call_cost(prefix, suffix, price_in, "write5" if write_mult == W5 else "write1h")
    writes = 1; reads = 0
    for g in gaps_min:
        if g <= ttl_min:
            total += call_cost(prefix, suffix, price_in, "read"); reads += 1
        else:
            total += call_cost(prefix, suffix, price_in, "write5" if write_mult == W5 else "write1h"); writes += 1
    return total, writes, reads

def keepalive_i_max(tau_min, w, r=READ):
    """Break-even idle horizon from the keepalive paper: I_max = tau * (w/r - 1)."""
    return tau_min * (w / r - 1)

def keepalive_cost_per_token(idle_min, tau_min, r=READ):
    """Cost of holding a prefix through an idle period, in units of the input price per token: (I/tau + 1) * r."""
    return (idle_min / tau_min + 1) * r

# ---- toy semantic cache -------------------------------------------------
def trigrams(text):
    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    return Counter(t[i:i + 3] for i in range(len(t) - 2))

def cosine(a, b):
    num = sum(v * b.get(k, 0) for k, v in a.items())
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0

TEMPLATES = [
    ("What is the data retention window for account {a}?", "retention:{a}"),
    ("How many days does workspace {a} keep deleted exports?", "exports:{a}"),
    ("Which support tier is account {a} on?", "tier:{a}"),
    ("When does the contract for account {a} renew?", "renew:{a}"),
]
PARAPHRASE = {
    0: ["How long is the retention period for account {a}?", "For account {a}, what is the data retention window?"],
    1: ["For how many days does workspace {a} retain deleted exports?", "How long are deleted exports kept for workspace {a}?"],
    2: ["What support tier does account {a} have?", "Account {a}: which support tier?"],
    3: ["What is the renewal date of the contract for account {a}?", "When will account {a} renew its contract?"],
}

def make_pairs(n=400, seed=18):
    """Pairs (q1, q2, same_answer). Half are paraphrases of the same question for the same account (answer reusable);
    half are the same question for a different account, or a different question for the same account (answer NOT reusable)."""
    rnd = random.Random(seed); out = []
    ids = [f"A-{rnd.randint(1000, 9999)}" for _ in range(60)]
    for i in range(n):
        t = rnd.randrange(len(TEMPLATES)); a = rnd.choice(ids)
        q1 = TEMPLATES[t][0].format(a=a)
        k = i % 4
        if k in (0, 1):
            out.append((q1, rnd.choice(PARAPHRASE[t]).format(a=a), True))
        elif k == 2:
            b = rnd.choice([x for x in ids if x != a])
            out.append((q1, TEMPLATES[t][0].format(a=b), False))
        else:
            t2 = rnd.choice([x for x in range(len(TEMPLATES)) if x != t])
            out.append((q1, TEMPLATES[t2][0].format(a=a), False))
    return out

def sweep(pairs, thresholds):
    sims = [(cosine(trigrams(a), trigrams(b)), same) for a, b, same in pairs]
    rows = []
    for th in thresholds:
        hits = [(s, same) for s, same in sims if s >= th]
        good = sum(1 for _, same in hits if same); bad = len(hits) - good
        rows.append({"threshold": th, "hit_rate": len(hits) / len(sims), "false_hits": bad,
                     "false_hit_share_of_hits": bad / len(hits) if hits else 0.0,
                     "safe_hit_rate": good / len(sims)})
    return rows

def expected_cost_per_query(row, call_usd, false_hit_penalty_usd):
    """Per query: a hit costs ~0 plus the penalty when false; a miss costs one call. Lookup cost ignored (stated in the text)."""
    n_hit = row["hit_rate"]; bad = n_hit * row["false_hit_share_of_hits"]
    return (1 - n_hit) * call_usd + bad * false_hit_penalty_usd

# ---- cache health from cost records -------------------------------------
def cache_health(records, min_prefix=1):
    """records: dicts with cache_read_tokens, cache_write_tokens, input_tokens. Flags a feature that writes repeatedly and never reads."""
    w = sum(r["cache_write_tokens"] for r in records); rd = sum(r["cache_read_tokens"] for r in records)
    inp = sum(r["input_tokens"] for r in records)
    total = w + rd + inp
    nwrites = sum(1 for r in records if r["cache_write_tokens"] >= min_prefix)
    nreads = sum(1 for r in records if r["cache_read_tokens"] >= min_prefix)
    return {"calls": len(records), "write_calls": nwrites, "read_calls": nreads,
            "read_share_of_input": rd / total if total else 0.0,
            "write_without_read": nwrites >= 3 and nreads == 0}
