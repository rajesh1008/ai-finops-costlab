"""Chapter 33: customer-facing caps against a population. Per-run costs are REAL (the 120 dependent-lookup agent runs of the Chapter 24 chain lab, haiku-4-5 placeholder rates).
The customers, their run counts and their types are SYNTHETIC and drawn here; plan price is ASSUMED. A cap is a function from a customer-month to (runs allowed, cost admitted)."""
import random, statistics

def make_customers(n, pool_easy, pool_hard, seed=0, mix=(0.90, 0.08, 0.02), plan=3.0):
    """Types: normal (lognormal run count, median 60, mixed run costs), heavy_task (same count, runs drawn only from the dearest half of the cost pool: a legitimate hard use),
    automated (5,000 to 20,000 cheap runs a month from the cheapest half of the pool: a script)."""
    rnd = random.Random(seed); out = []
    for i in range(n):
        u = rnd.random()
        if u < mix[0]: t = "normal"; k = max(1, int(rnd.lognormvariate(4.09, 0.8))); runs = [rnd.choice(pool_easy + pool_hard) for _ in range(k)]
        elif u < mix[0] + mix[1]: t = "heavy_task"; k = max(1, int(rnd.lognormvariate(4.09, 0.8))); runs = [rnd.choice(pool_hard) for _ in range(k)]
        else: t = "automated"; k = rnd.randint(5000, 20000); runs = [rnd.choice(pool_easy) for _ in range(k)]
        out.append({"id": i, "type": t, "runs": runs, "plan": plan})
    return out

def apply_cap(customer, kind, value):
    """Return (runs_served, cost_admitted). kind: 'runs' (hard count cap), 'cost' (dollar cap per month, admit runs while cumulative cost <= cap), 'none'."""
    cs = customer["runs"]
    if kind == "none": return len(cs), sum(cs)
    if kind == "runs": s = cs[:int(value)]; return len(s), sum(s)
    if kind == "cost":
        tot = 0.0; n = 0
        for c in cs:
            if tot + c > value: break
            tot += c; n += 1
        return n, tot
    raise ValueError(kind)

def evaluate(customers, kind, value):
    """Per type: share of customers who lose any run, share of runs lost, and the margin (plan - admitted cost) summed."""
    by = {}
    for c in customers:
        n, cost = apply_cap(c, kind, value); b = by.setdefault(c["type"], {"n": 0, "hit": 0, "runs": 0, "lost": 0, "cost_admitted": 0.0, "cost_total": 0.0, "plan": 0.0, "neg_margin": 0})
        b["n"] += 1; b["hit"] += (n < len(c["runs"])); b["runs"] += len(c["runs"]); b["lost"] += len(c["runs"]) - n
        b["cost_admitted"] += cost; b["cost_total"] += sum(c["runs"]); b["plan"] += c["plan"]; b["neg_margin"] += (cost > c["plan"])
    return by
