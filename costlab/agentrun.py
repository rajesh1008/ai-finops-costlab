"""Chapter 24: arithmetic over recorded agent runs. A run is a list of steps; each step has input_tokens and output_tokens (as billed by the API)."""
import math

def step_cost(inp, out, usd_in, usd_out):
    return inp / 1e6 * usd_in + out / 1e6 * usd_out

def run_cost(steps, usd_in, usd_out):
    return sum(step_cost(s["in"], s["out"], usd_in, usd_out) for s in steps)

def quantile(xs, q):
    xs = sorted(xs)
    if not xs: raise ValueError("empty")
    pos = (len(xs) - 1) * q; lo = int(math.floor(pos)); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)

def spread(xs):
    """max/min ratio, p90/p50 ratio, and mean/median ratio of a list of run costs."""
    xs = [x for x in xs if x > 0]
    return {"max_over_min": max(xs) / min(xs), "p90_over_p50": quantile(xs, .9) / quantile(xs, .5), "mean_over_median": (sum(xs) / len(xs)) / quantile(xs, .5)}

def repeat_spread(by_task):
    """For each task with >= 2 repeats, max/min cost across repeats. Returns the list."""
    return [max(v) / min(v) for v in by_task.values() if len(v) >= 2 and min(v) > 0]

def input_share_of_steps(steps):
    """Share of billed input tokens that were already present in the previous step's input (re-read history)."""
    total = sum(s["in"] for s in steps)
    if len(steps) < 2 or total == 0: return 0.0
    reread = sum(min(steps[i]["in"], steps[i - 1]["in"] + steps[i - 1]["out"]) for i in range(1, len(steps)))
    return reread / total

def step_budget_for(costs, coverage=0.95):
    """Smallest budget in dollars that covers `coverage` of observed runs."""
    return quantile(costs, coverage)

def cost_if_capped(costs, cap):
    """Total spend if every run is stopped at `cap` dollars, and how many runs were cut."""
    cut = sum(1 for c in costs if c > cap)
    return sum(min(c, cap) for c in costs), cut
