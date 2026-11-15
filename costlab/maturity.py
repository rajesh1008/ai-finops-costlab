"""Chapter 41: an AI FinOps maturity rubric that asks for artefacts, a scorer with a no-skipping rule, and 48 SYNTHETIC evidence statements with AUTHOR-ASSIGNED level labels
(8 capabilities x 6: a plain crawl, a plain walk, a plain run, and three decoys that sound more mature than their evidence). Levels: 0 crawl, 1 walk, 2 run (the FinOps Foundation's crawl, walk, run vocabulary).
The rubric is my construction, mapped to book chapters; it is not the Foundation's assessment."""
LEVELS = ["crawl", "walk", "run"]
CAPS = ["allocation", "metering", "unit_economics", "forecasting", "anomaly", "budgets", "commitments", "governance"]
WEIGHT = {c: 1.0 for c in CAPS}   # equal weights; a team may reweight
# Artefact required for each level (level 0 needs none). The evidence check is "can you show the artefact".
ARTEFACT = {
    "allocation":     ["", "key-to-owner map and a weekly coverage figure", "coverage reconciled to the invoice, with the untagged remainder owned and aged"],
    "metering":       ["", "gateway log with one record per call", "records reconciled to the invoice line by line within a stated tolerance, monthly"],
    "unit_economics": ["", "cost per outcome for one product, outcome signed by its owner", "cost per outcome for every material product with failures in the numerator, as a distribution, in the board pack"],
    "forecasting":    ["", "driver-based forecast with a backtest", "driver forecast with an error budget, variance split by driver and a register of changes"],
    "anomaly":        ["", "daily alerts on spend", "rate alerts per product with an owner and runbook, replayed on history, time to stop measured"],
    "budgets":        ["", "per-team budgets with an alert at a threshold", "caps enforced before the call at the gateway, a degradation ladder, exceptions logged"],
    "commitments":    ["", "one commitment sized from measured usage", "commitments modelled against model-change scenarios, exit terms and shortfall exposure tracked"],
    "governance":     ["", "written policy and a recurring review", "policy as code, a reproducible evidence pack, a gate on model changes"],
}

def level_from_evidence(have):
    """`have` is the highest level whose artefact the team can show, per capability, as a list of booleans [walk_ok, run_ok]. No skipping: run counts only if walk is shown."""
    walk, run = have
    if walk and run: return 2
    if walk: return 1
    return 0

def score(levels, weight=WEIGHT):
    """0 to 100: each capability contributes level/2 of its weight."""
    tot = sum(weight[c] for c in CAPS)
    return 100.0 * sum(weight[c] * levels[c] / 2.0 for c in CAPS) / tot

def weakest(levels):
    m = min(levels.values()); return [c for c in CAPS if levels[c] == m]

def inflation(self_levels, shown_levels):
    """Per capability, self-reported minus shown. Positive means the self-assessment is above the evidence."""
    return {c: self_levels[c] - shown_levels[c] for c in CAPS}

def gaming_example():
    """A score built from one capability's coverage number can be raised without changing the bill: tagging everything 'shared' lifts coverage to 100 percent."""
    total = 100.0; attributed_real = 38.0; to_shared = 62.0
    return {"coverage_before": attributed_real / total, "coverage_after_dumping_into_shared": (attributed_real + to_shared) / total, "owned_spend_share_after": attributed_real / total}

S = {}
# (statement, true_level, kind)  kind: plain or decoy
S["allocation"] = [
 ("Finance reads the provider invoices once a month and splits them by gut feel between product teams.", 0, "plain"),
 ("Each API key maps to a named owning team, and a coverage figure is posted every Monday; last week it was 86 percent.", 1, "plain"),
 ("Coverage reconciles to the invoice each month at 97 percent; the untagged remainder has an owner and an ageing report, oldest item 11 days.", 2, "plain"),
 ("We have best-in-class attribution; everyone knows which team owns which spend.", 0, "decoy"),
 ("Keys map to owners and coverage is tracked weekly at 90 percent, and we plan to reconcile it to the invoice by next year.", 1, "decoy"),
 ("Coverage is 99 percent because anything we cannot place goes into a shared bucket that the platform team owns.", 1, "decoy"),
]
S["metering"] = [
 ("We look at the provider dashboards when the bill surprises us.", 0, "plain"),
 ("Every model call goes through a gateway that writes one record with model, tokens, owner and cost.", 1, "plain"),
 ("Gateway records are reconciled line by line to the invoice every month; the tolerance is 0.5 percent and the last gap was a credit note.", 2, "plain"),
 ("We have full observability of our AI stack with a modern tracing platform.", 0, "decoy"),
 ("The gateway records every call and its cost, and the finance team trusts the totals.", 1, "decoy"),
 ("Our records match the invoice in total each month, so reconciliation is done.", 1, "decoy"),
]
S["unit_economics"] = [
 ("We track cost per token and cost per call, and both are falling.", 0, "plain"),
 ("The support assistant has a cost per resolved ticket, with 'resolved' defined and signed by its product owner.", 1, "plain"),
 ("All six material products report cost per outcome with retries and failures in the numerator, as median and 95th percentile, and the board pack carries it.", 2, "plain"),
 ("Our unit economics are strong; margin on AI features is healthy across the board.", 0, "decoy"),
 ("Cost per outcome is reported for three of six products, with failures included, and the board sees a summary.", 1, "decoy"),
 ("We report cost per successful task for every product as an average, excluding retried runs.", 1, "decoy"),
]
S["forecasting"] = [
 ("The forecast is last month's bill plus twenty percent.", 0, "plain"),
 ("A driver model (calls, tokens per call, price, mix) is backtested over the last six months with a median error of 11 percent.", 1, "plain"),
 ("The driver forecast carries an error budget, monthly variance is split by driver, and every price or model change is entered in a register of changes.", 2, "plain"),
 ("We use advanced predictive analytics for AI spend forecasting.", 0, "decoy"),
 ("The forecast has drivers and a backtest, and a register of changes is planned for next quarter.", 1, "decoy"),
 ("We forecast by driver and variance is explained every month, though we have never backtested it.", 0, "decoy"),
]
S["anomaly"] = [
 ("We spot spikes in the monthly review meeting.", 0, "plain"),
 ("A daily spend alert fires to a channel when spend exceeds 130 percent of the trailing average.", 1, "plain"),
 ("Alerts are on call-rate and cost-per-session by product, each with an owner and a runbook; they were replayed on 90 days of history and time to stop is measured at 14 minutes median.", 2, "plain"),
 ("Our AI-powered anomaly detection catches issues before they affect the bill.", 0, "decoy"),
 ("We have per-product rate alerts with owners and runbooks, but have never replayed them on history.", 1, "decoy"),
 ("Daily alerts fire and someone usually looks, and the last incident was stopped in about an hour.", 1, "decoy"),
]
S["budgets"] = [
 ("Budgets live in a spreadsheet that finance updates quarterly.", 0, "plain"),
 ("Each team has a monthly budget and an alert at 80 percent, which goes to the team lead.", 1, "plain"),
 ("Caps are enforced at the gateway before the call, with a degradation ladder per product and an exceptions log reviewed weekly.", 2, "plain"),
 ("We have robust budget controls across the organisation.", 0, "decoy"),
 ("Caps are written into the agent framework configuration and agents stop when they hit them.", 0, "decoy"),
 ("Hard caps exist at the gateway for the two biggest products; the other five have an 80 percent alert only.", 1, "decoy"),
]
S["commitments"] = [
 ("Everything is pay as you go.", 0, "plain"),
 ("We bought one spend commitment, sized at 70 percent of the last three months of measured usage.", 1, "plain"),
 ("Each commitment was modelled against three model-change scenarios; exit terms are summarised and shortfall exposure is tracked monthly.", 2, "plain"),
 ("We negotiate hard and have strong commercial terms with all vendors.", 0, "decoy"),
 ("We have a commitment sized from usage and plan to model the effect of a model change at renewal.", 1, "decoy"),
 ("We model shortfall exposure monthly for a commitment that was sized from a vendor's forecast, not our usage.", 0, "decoy"),
]
S["governance"] = [
 ("Nobody has written down who may change a model or a cap.", 0, "plain"),
 ("A written AI cost policy exists and the platform and finance leads review spend every two weeks.", 1, "plain"),
 ("Cost rules are policy as code, the evidence pack rebuilds from the ledger with one command, and a model change cannot ship without the cost and quality gate.", 2, "plain"),
 ("We take AI governance very seriously and have a mature framework.", 0, "decoy"),
 ("We have a written policy and a regular review, and our rules are mostly enforced by convention.", 1, "decoy"),
 ("Rules are policy as code and the evidence pack rebuilds, but model changes ship without a gate.", 1, "decoy"),
]
STATEMENTS = [{"cap": c, "text": t, "true": lv, "kind": k} for c in CAPS for (t, lv, k) in S[c]]

# Seat-heavy variants (Ch41, second setting): artefacts for spend that arrives as seats, add-ons and credits.
SEAT_ARTEFACT = {
    "metering":   ["", "seat inventory with owner and last-used date from the vendor admin report", "seats and add-on lines reconciled to the invoice monthly; credits drawn against the contract tracked"],
    "allocation": ["", "each seat mapped to a cost centre", "cost centre figures reconciled to the invoice; unassigned and inactive seats owned and aged"],
    "budgets":    ["", "seat cap per team and a quarterly review of inactive seats", "seat reclamation automated after a stated inactivity period, exceptions logged"],
}

def idle_seat_cost(seats, usd_per_seat_month, idle_share):
    """Annual cost of seats unused in the last 30 days. ILLUSTRATIVE inputs in the chapter."""
    return seats * usd_per_seat_month * 12 * idle_share
