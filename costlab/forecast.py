"""Chapter 13: driver-based forecast against a trend line, with an error budget. SYNTHETIC history; assumptions stated by caller."""
import random, statistics


def history(months=18, seed=13, users0=2000, growth=0.07, tasks0=22.0, tasks_drift=0.03, cost0=0.30, cost_drift=-0.01,
            price_cut_month=13, price_cut=0.35, agent_launch_month=9, agent_tasks_mult=1.6, noise=0.04):
    """Return list of dicts per month: users, tasks_per_user, cost_per_task, spend. Events: an agent launch raises tasks and cost per task;
    a vendor price cut lowers cost per task by price_cut from price_cut_month."""
    rnd = random.Random(seed)
    out = []
    users = users0; tpu = tasks0; cpt = cost0
    for m in range(1, months + 1):
        users *= 1 + growth * rnd.uniform(0.6, 1.4)
        tpu *= 1 + tasks_drift
        cpt *= 1 + cost_drift
        t_eff = tpu * (agent_tasks_mult if m >= agent_launch_month else 1.0)
        c_eff = cpt * (1.25 if m >= agent_launch_month else 1.0) * ((1 - price_cut) if m >= price_cut_month else 1.0)
        n = rnd.lognormvariate(0, noise)
        out.append({"m": m, "users": users, "tpu": t_eff, "cpt": c_eff, "spend": users * t_eff * c_eff * n})
    return out


def trend_forecast(hist, upto, horizon, window=6):
    """Fit a log-linear trend to the last `window` months before month `upto` and project."""
    ys = [h["spend"] for h in hist if h["m"] <= upto][-window:]
    import math
    xs = list(range(len(ys)))
    lx = [math.log(y) for y in ys]
    xm = statistics.mean(xs); ym = statistics.mean(lx)
    b = sum((x - xm) * (l - ym) for x, l in zip(xs, lx)) / sum((x - xm) ** 2 for x in xs)
    a = ym - b * xm
    return [math.exp(a + b * (len(ys) - 1 + k)) for k in range(1, horizon + 1)]


def driver_forecast(hist, upto, horizon, user_growth, tpu_growth, cpt_change_by_month=None):
    """Spend = users x tasks per user x cost per task, each projected with an explicit assumption."""
    last = [h for h in hist if h["m"] == upto][0]
    cpt_change_by_month = cpt_change_by_month or {}
    users, tpu, cpt = last["users"], last["tpu"], last["cpt"]
    out = []
    for k in range(1, horizon + 1):
        users *= 1 + user_growth; tpu *= 1 + tpu_growth
        cpt *= 1 + cpt_change_by_month.get(upto + k, 0.0)
        out.append(users * tpu * cpt)
    return out


def mape(pred, actual):
    return statistics.mean(abs(p - a) / a for p, a in zip(pred, actual))


def monte_carlo(last, horizon, user_g=(0.04, 0.10), tpu_g=(0.0, 0.06), cpt_g=(-0.03, 0.02), n=4000, seed=5):
    """Spend in the final month of the horizon under uniform ranges on three monthly drivers. Returns sorted samples."""
    rnd = random.Random(seed)
    s = []
    for _ in range(n):
        ug = rnd.uniform(*user_g); tg = rnd.uniform(*tpu_g); cg = rnd.uniform(*cpt_g)
        s.append(last["users"] * (1 + ug) ** horizon * last["tpu"] * (1 + tg) ** horizon * last["cpt"] * (1 + cg) ** horizon)
    s.sort()
    return s
