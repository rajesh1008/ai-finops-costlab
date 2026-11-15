"""Chapter 11: cost per successful task (CPST). SYNTHETIC tasks; every rate is an assumption stated by the caller.

Rule from the protocol sources: every initiated task adds its cost to the numerator, successful or not;
only tasks that pass the pre-agreed success rule count in the denominator.
"""
import random
from dataclasses import dataclass


@dataclass
class Task:
    tid: int
    kind: str
    attempts: int
    model_usd: float
    tool_usd: float
    verify_usd: float
    human_min: float
    success: bool


def simulate(n=5000, seed=11, p_easy=0.85, p_hard=0.35, hard_share=0.25, retry_cap=2,
             easy_cost=0.012, hard_cost=0.06, tool=0.002, verify=0.003, human_rate_per_min=0.80,
             human_min_on_fail=4.0, correlated=True):
    """Each task has a kind; each attempt costs about easy_cost or hard_cost (lognormal spread).
    If correlated, a hard task that fails once keeps its low success probability on a retry; if not, retries are independent draws."""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        hard = rnd.random() < hard_share
        p = p_hard if hard else p_easy
        base = hard_cost if hard else easy_cost
        attempts = 0; model = 0.0; toolc = 0.0; ver = 0.0; ok = False
        while attempts < retry_cap and not ok:
            attempts += 1
            model += base * rnd.lognormvariate(0, 0.5)
            toolc += tool * (3 if hard else 1)
            ver += verify
            if attempts == 1:
                ok = rnd.random() < p
            else:
                ok = rnd.random() < (p * 0.5 if correlated else p)
        hm = 0.0 if ok else human_min_on_fail
        out.append(Task(i, "hard" if hard else "easy", attempts, model, toolc, ver, hm, ok))
    return out, human_rate_per_min


def total(t: Task, rate: float, include_human=True):
    return t.model_usd + t.tool_usd + t.verify_usd + (t.human_min * rate if include_human else 0.0)


def report(tasks, rate, include_human=True):
    n = len(tasks); s = sum(1 for t in tasks if t.success)
    cost_all = sum(total(t, rate, include_human) for t in tasks)
    cost_ok = sum(total(t, rate, include_human) for t in tasks if t.success)
    return {"tasks": n, "successes": s, "success_rate": s / n, "cost_all": cost_all, "cost_succ_only": cost_ok,
            "cpst": cost_all / s if s else None, "mean_cost_of_successes": cost_ok / s if s else None,
            "per_attempted": cost_all / n, "failed_cost_share": 1 - cost_ok / cost_all}


def by_kind(tasks, rate, include_human=True):
    res = {}
    for k in ("easy", "hard"):
        sub = [t for t in tasks if t.kind == k]
        res[k] = report(sub, rate, include_human)
    return res
