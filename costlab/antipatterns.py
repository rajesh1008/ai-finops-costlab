"""Chapter 46: thirty anti-patterns, each with the control that stops it and a short vignette (synthetic, written by the author) used by the classification lab.
Tuple: (id, name, control, chapter reference, vignette)."""
AP = [
("A01", "Reporting the mean", "Report median and p95 per run and per user.", "7", "The dashboard shows an average cost per session of 2 cents. Nobody has looked at the most expensive 5 percent of sessions, which cost about 6 cents each."),
("A02", "Price-per-token comparison", "Compare cost per successful task, not list price.", "11", "A team moves to a model whose list price is ten times lower and reports a 90 percent saving from the price sheet alone, without re-running the task set."),
("A03", "Untagged shared key", "One key per service, attribution at the gateway.", "5", "Six services share one API key. At month end the invoice is one line and finance asks engineering to guess the split."),
("A04", "Savings counted twice", "One savings ledger with states and lever interaction.", "43", "Caching is credited with 40 percent savings and retrieval with 50 percent, both against the same old baseline, and the two are added to claim 90 percent."),
("A05", "Cap without fallback", "Build the degradation ladder before enforcing the cap.", "27", "A hard monthly budget cuts off customer-facing answers with an error page when it is reached. Customers see an outage on the 26th of every month."),
("A06", "Alert on the daily total", "Alert on spend rate per key per minute.", "10", "A loop starts at 2 a.m. The daily-spend alert is set at a threshold that will be crossed at about 9 a.m."),
("A07", "Exception without expiry", "Every exception has an owner and an expiry or the log rejects it.", "44", "Eleven budget exceptions were granted last quarter. Four have no end date and two belong to people who left the company."),
("A08", "Prompt trimmed under the cache minimum", "Price the change with the cache in the model.", "39", "An engineer halves a long prompt to save tokens. The prompt now falls below the model's minimum cacheable length and the bill per call rises."),
("A09", "Model swap on a list-price estimate", "Replay a held-out set through every gate before a model change.", "35", "A newer, cheaper model is swapped in after a one-line price comparison. Two weeks later the output format has broken on one template and support tickets climb."),
("A10", "Tolerance on the total only", "Reconcile at line level, not on the invoice total.", "34", "Finance accepts the invoice because the total is within 1 percent of the usage-based estimate. A duplicate charge and an offsetting credit hide inside it."),
("A11", "Savings that never reach the invoice", "Track identified, committed and realised savings separately.", "43", "The team reports 60,000 dollars a month of identified savings. Three months later the invoice has not moved and nobody can say which items were done."),
("A12", "Unit cost with no quality bar", "State the quality bar next to every unit cost.", "11", "Cost per ticket falls 30 percent after a change. Nobody checked whether resolution quality fell with it."),
("A13", "Commitment sized on today's mix", "Size commitments on scenarios in which the work moves.", "30", "A 15 percent discount is bought against a forecast of spend on one model. A year later most work has moved to a cheaper model and the commitment is a fixed charge."),
("A14", "Vendor lock-in by prompt", "Keep a portability test and a second model that passes it.", "31", "Prompts depend on one vendor's response format. A price rise cannot be answered by moving, because no one has tried a second model since launch."),
("A15", "Policy in a wiki", "Cost policy as code with tests, not as a document.", "32", "The rule that expensive models need approval is on a wiki page. In the usage log 76 percent of spend on those models has no approval record."),
("A16", "Per-customer cap on cost alone", "Test caps against heavy and ordinary users before launch.", "33", "A customer-facing cap is set in dollars. Customers with long, legitimate tasks hit it twice as often as customers with short ones, and complain."),
("A17", "Showback nobody reads", "Put the number in front of the person who can change it, with a decision attached.", "36", "A monthly showback goes to forty people. In six months no team has changed a prompt, a model or a budget because of it."),
("A18", "Chargeback on a flawed allocation", "Validate allocation rules against a known case before charging.", "36", "Shared cache costs are split by call count. A team that wrote the cached prompt pays less than teams that merely read it."),
("A19", "One person owns it all", "Name the roles and the escalation path in the operating model.", "37", "A single analyst runs the AI cost report, the budget, the anomaly queue and the vendor call. When she is on leave, nothing is reviewed."),
("A20", "Buy the tool, skip the meter", "Instrument first, buy second, and test the tool on your own data.", "38", "A cost platform is bought before the services emit usage records. Dashboards are full of unallocated spend."),
("A21", "Estimator on list price", "Test the estimator against measured cost on past changes.", "39", "A pull-request bot posts a price estimate for each prompt change. It has never been checked against what the change actually cost."),
("A22", "Board pack of tokens", "Report cost per outcome with loaded costs and an interval.", "40", "The board pack shows tokens consumed and cost per million tokens. No page shows what a resolved ticket or a closed deal costs."),
("A23", "Maturity by self-assessment", "Gate each level on an artefact and a no-skipping rule.", "41", "A team rates itself at walk on every dimension. Asked for the artefacts that prove it, it can produce two."),
("A24", "Coverage by percent, not by dollars", "Report coverage by spend and list what is unowned.", "42", "Tag coverage is reported as 92 percent of requests. The 8 percent untagged are the largest and most expensive services."),
("A25", "Optimisation before the meter", "Order of work: meter, owner, forecast, then levers.", "43", "A team spends a quarter rewriting prompts to save money before it can say what the current spend per feature is."),
("A26", "No stop authority", "Name who may switch an agent off without asking, in the runbook.", "44", "During a night incident the on-call engineer waits 40 minutes for the product owner to approve disabling the key."),
("A27", "Forecast as one number", "Publish an interval and the volume and rate decomposition.", "13", "The forecast for next quarter is a single figure. When actual spend is 30 percent above it, nobody can say whether volume or price per call moved."),
("A28", "Evidence assembled at audit time", "Keep the evidence pack current as a by-product of operation.", "34", "When an auditor asks how a figure was derived, the team spends two weeks rebuilding logs and spreadsheets from memory."),
("A29", "Benchmark borrowed as a target", "Use external numbers as questions, not targets; compute your own.", "14", "The leadership asks for the savings rate 'the industry achieves' after reading a vendor survey, and sets it as the team's goal."),
("A30", "No rehearsal", "Rehearse the stop and the failover each quarter and time them.", "26", "The runbook for stopping a runaway agent has never been exercised. The first time it is used is the first incident."),
]
def ids(): return [a[0] for a in AP]
def name_of(i): return next(a[1] for a in AP if a[0] == i)
def score(pred, truth): return sum(1 for p, t in zip(pred, truth) if p == t) / len(truth)

# --- offline baseline: a bag-of-words matcher, no model. Used by scripts/antipattern_baseline.py ---
import math, re
from collections import Counter
STOP = set("a an the of to in on and or is are was were be been it its for with at by as that this from has have had not no but so than then into out up over after before when which who they their them his her she he we you your our i".split())
def toks(s): return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 1]
def tfidf_match(vignette, docs):
    """Return the index of the doc with the highest cosine similarity to the vignette, using idf over docs."""
    df = Counter(w for d in docs for w in set(toks(d))); n = len(docs)
    idf = lambda w: math.log((n + 1) / (df.get(w, 0) + 1)) + 1
    def vec(s): c = Counter(toks(s)); return {w: v * idf(w) for w, v in c.items()}
    def cos(a, b):
        num = sum(a[w] * b.get(w, 0) for w in a); den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
        return num / den if den else 0
    q = vec(vignette); sc = [cos(q, vec(d)) for d in docs]
    return max(range(n), key=lambda i: sc[i])
