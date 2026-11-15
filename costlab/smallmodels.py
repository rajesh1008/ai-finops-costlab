"""Chapter 21: ticket-intent task, a pure-python student, and ownership break-even arithmetic. Tickets are SYNTHETIC. Build costs are ASSUMED inputs."""
import random, math, re
from collections import Counter, defaultdict

INTENTS = ["refund", "cancel", "invoice_copy", "plan_change", "login_help", "data_export", "bug_report", "pricing_question"]
PRIMARY = {
 "refund": ["I want my money back for this month", "please refund the charge from the fifth", "I was billed twice and need that returned"],
 "cancel": ["please close my account at the end of the term", "I would like to stop the subscription altogether", "cancel everything on our workspace from next cycle"],
 "invoice_copy": ["could you send me a PDF of last month's invoice", "I need a copy of the receipt for our accountant", "where can I download the invoice for March"],
 "plan_change": ["we want to move from the Team tier to Business", "can I downgrade to the smaller plan before renewal", "switch our seats to the annual plan please"],
 "login_help": ["I cannot sign in and the reset link never arrives", "my login keeps failing after the password change", "locked out of the dashboard since this morning"],
 "data_export": ["I need a full export of our workspace data", "how do I get all of our records out as CSV", "please send an archive of everything we stored"],
 "bug_report": ["the report page crashes when I pick a date range", "charts show blank after the last update", "the scheduled email did not run and shows an error"],
 "pricing_question": ["how much would fifty extra seats cost", "what is the price difference between the tiers", "do you charge per user or per workspace"],
}
DISTRACT = ["Last month I asked about {x}, but that is sorted now.", "A colleague mentioned {x}, though that is not why I am writing.",
            "(Unrelated: we once discussed {x}.)"]
CUE = {"refund": "a refund", "cancel": "cancelling", "invoice_copy": "an invoice copy", "plan_change": "a plan change", "login_help": "login trouble",
       "data_export": "a data export", "bug_report": "a bug", "pricing_question": "pricing"}
def _typo(s, rnd):
    if rnd.random() < 0.3 and len(s) > 20:
        i = rnd.randrange(5, len(s) - 3); s = s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return s
def make_tickets(n=600, seed=21):
    rnd = random.Random(seed); out = []
    for i in range(n):
        y = INTENTS[i % len(INTENTS)]
        s = rnd.choice(PRIMARY[y])
        if rnd.random() < 0.55:
            other = rnd.choice([k for k in INTENTS if k != y])
            d = rnd.choice(DISTRACT).format(x=CUE[other])
            s = (d + " " + s) if rnd.random() < 0.5 else (s + ". " + d)
        out.append({"id": i, "text": _typo(s, rnd), "label": y})
    rnd.shuffle(out)
    return out

PRECEDENCE = ["cancel", "refund", "data_export", "plan_change", "invoice_copy", "login_help", "bug_report", "pricing_question"]
def make_tickets_hard(n=600, seed=22):
    """Hard variant: 60 percent of tickets carry TWO real requests joined by 'and also'. Gold is the higher intent in PRECEDENCE (a stated business rule)."""
    rnd = random.Random(seed); out = []
    for i in range(n):
        a = INTENTS[i % len(INTENTS)]
        if rnd.random() < 0.6:
            b = rnd.choice([k for k in INTENTS if k != a])
            s = rnd.choice(PRIMARY[a]) + ", and also " + rnd.choice(PRIMARY[b]).lower()
            y = min((a, b), key=PRECEDENCE.index)
        else:
            s = rnd.choice(PRIMARY[a]); y = a
        out.append({"id": i, "text": _typo(s, rnd), "label": y})
    rnd.shuffle(out); return out

def tokens(t):
    w = re.findall(r"[a-z']+", t.lower())
    return w + [a + "_" + b for a, b in zip(w, w[1:])]

class NB:
    """Multinomial naive Bayes with add-one smoothing."""
    def fit(self, texts, labels):
        self.cc = Counter(labels); self.wc = defaultdict(Counter); self.V = set()
        for t, y in zip(texts, labels):
            for w in tokens(t): self.wc[y][w] += 1; self.V.add(w)
        self.tot = {y: sum(c.values()) for y, c in self.wc.items()}; self.n = len(labels); return self
    def predict(self, t):
        best, bs = None, -1e18
        for y in self.cc:
            s = math.log(self.cc[y] / self.n)
            for w in tokens(t): s += math.log((self.wc[y][w] + 1) / (self.tot[y] + len(self.V) + 1))
            if s > bs: best, bs = y, s
        return best

def accuracy(pred, gold):
    return sum(p == g for p, g in zip(pred, gold)) / len(gold)

def breakeven_requests(build_usd, cost_now, cost_new):
    """distil labs form: build / (current per request - new per request). inf when the new path is not cheaper."""
    d = cost_now - cost_new
    return math.inf if d <= 0 else build_usd / d

def breakeven_months(train_usd, refresh_quarterly_usd, horizon_quarters, monthly_saving):
    """AWS Well-Architected form: (one-time + quarterly refresh x horizon quarters) / monthly saving."""
    return math.inf if monthly_saving <= 0 else (train_usd + refresh_quarterly_usd * horizon_quarters) / monthly_saving

def per_request_selfhost(monthly_fixed_usd, monthly_requests):
    return monthly_fixed_usd / monthly_requests

def utilisation_cost_per_1k(gpu_hourly, requests_per_sec_full, utilisation):
    return gpu_hourly / (3600 * requests_per_sec_full * utilisation) * 1000
