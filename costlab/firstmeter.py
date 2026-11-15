"""Chapter 42: the first quarter. SYNTHETIC untagged requests for four Fieldstone features, a label parser, spend-weighted scoring,
a weekly coverage trajectory and an invoice residual calculation. All traffic is synthetic and author-written; feature mix, token weights and
prices are ASSUMED."""
import random, json, re

FEATURES = {
    "support_assistant": {"system": "You are Fieldstone's support assistant. Answer using the handbook clauses only and quote the clause reference.", "weight_tokens": 6200},
    "report_summariser": {"system": "You summarise a Fieldstone weekly analytics report for an executive in five bullet points.", "weight_tokens": 3100},
    "sql_helper": {"system": "You write read-only SQL for the Fieldstone warehouse from a plain-language question. Return one query.", "weight_tokens": 900},
    "onboarding_emailer": {"system": "You draft a short onboarding email for a new Fieldstone workspace owner. Friendly, under 120 words.", "weight_tokens": 700},
}
NAMES = list(FEATURES)
USER = {
    "support_assistant": ["A customer on tier {n} asks how to export their workspace data. What do I say?", "Customer wants deletion confirmed for workspace WS-{n}. Which retention window applies?", "Does a tier {n} account owner need verifying before a deletion request?"],
    "report_summariser": ["Report for week {n}: sessions up 4 percent, churned workspaces 3, new dashboards 112. Summarise.", "Week {n} analytics: median query time 1.8 seconds, failed scheduled exports 7. Summarise for the executive team.", "Summarise this weekly report for week {n}: active users 3,812, seats 5,200, support tickets 241."],
    "sql_helper": ["How many workspaces created a dashboard in the last {n} days?", "List the ten workspaces with the most scheduled exports in week {n}.", "Average query time by tier for the last {n} days, please."],
    "onboarding_emailer": ["New owner Priya at workspace WS-{n}, she signed up from a webinar. Draft the welcome email.", "Draft the day-{n} check-in email for a new workspace owner who has not yet invited anyone.", "Welcome email for owner Tomas, workspace WS-{n}, he has already connected one data source."],
}
def make_requests(per_feature=40, seed=42):
    rng = random.Random(seed); out = []
    for f in NAMES:
        for i in range(per_feature):
            u = rng.choice(USER[f]).format(n=rng.randint(2, 90))
            tok = int(FEATURES[f]["weight_tokens"] * rng.uniform(0.8, 1.25))
            out.append({"id": f"{f[:3]}-{i:02d}", "feature": f, "system": FEATURES[f]["system"], "user": u, "tokens": tok})
    rng.shuffle(out); return out

def parse_label(text):
    m = re.search(r'"feature"\s*:\s*"([a-z_]+)"', text or "")
    if m: v = m.group(1)
    else:
        v = next((n for n in NAMES if n in (text or "")), "unparsed")
    return v if v in NAMES or v == "unknown" else "unparsed"

def score(rows, price_per_token=1e-6):
    """rows: list of dict(feature, label, tokens). Accuracy, and spend-weighted outcome: dollars landing on the wrong owner, dollars left unknown."""
    n = len(rows); right = sum(r["label"] == r["feature"] for r in rows)
    spend = sum(r["tokens"] for r in rows) * price_per_token
    wrong = sum(r["tokens"] for r in rows if r["label"] not in (r["feature"], "unknown", "unparsed")) * price_per_token
    unk = sum(r["tokens"] for r in rows if r["label"] in ("unknown", "unparsed")) * price_per_token
    return {"n": n, "right": right, "accuracy": right / n if n else 0.0, "spend": spend, "misattributed": wrong, "unknown": unk,
            "wrong_share": wrong / spend if spend else 0.0, "unknown_share": unk / spend if spend else 0.0}

def confusion(rows):
    c = {}
    for r in rows: c[(r["feature"], r["label"])] = c.get((r["feature"], r["label"]), 0) + 1
    return c

def coverage_trajectory(weeks=13, start=0.38, gain=0.11, cap=0.93):
    """ASSUMED weekly tagged share of spend: climbs by `gain` of the remaining gap each week toward `cap`."""
    out, c = [], start
    for w in range(1, weeks + 1):
        out.append(round(c, 4)); c = c + (cap - c) * gain
    return out

def residual(invoice, ledger):
    """Settlement versus attribution: unexplained share of the invoice (shadow or unmetered spend, or a billing error)."""
    return {"residual_usd": invoice - ledger, "residual_share": (invoice - ledger) / invoice if invoice else 0.0}

def first_honest_number(spend, tagged, outcomes_signed):
    """The first honest number is cost per signed outcome on the tagged share, with the untagged share printed beside it."""
    cov = tagged / spend if spend else 0.0
    return {"coverage": cov, "cost_per_outcome": tagged / outcomes_signed if outcomes_signed else float("inf"), "untagged_usd": spend - tagged,
            "upper_bound_per_outcome": spend / outcomes_signed if outcomes_signed else float("inf")}
