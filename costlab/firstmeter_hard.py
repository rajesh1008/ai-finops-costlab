"""Chapter 42 follow-up (nineteenth run): a HARD variant of the owner-recovery lab. SYNTHETIC, author-written requests for four features whose user messages overlap
(all concern workspace metrics), with a generic system prompt shared by every feature in view G. Ground truth is the feature that generated the template; two template
families (metric_explainer vs support_assistant) are deliberately close and some labels are contestable. Reuses parse_label, score and confusion from firstmeter."""
import random
from costlab.firstmeter import NAMES as _OLD, parse_label, score, confusion  # noqa: F401
HARD = ["sql_helper", "report_summariser", "metric_explainer", "support_assistant"]
GENERIC = "You are a helpful assistant for Fieldstone Analytics."
USER = {
    "sql_helper": ["Which workspaces had more than {n} failed exports last week?", "Show weekly active users by tier for the last {n} days.", "Count scheduled exports per workspace for week {n}, highest first."],
    "report_summariser": ["Week {n}: failed exports 7, active users 3,812, median query time 1.8 seconds. Summarise for the exec team.", "Summarise this week {n} report: churned workspaces 3, new dashboards 112, failed exports 9.", "Exec summary please. Week {n}: active users 3,904, tickets 233, failed exports 5."],
    "metric_explainer": ["Why would failed exports rise in week {n}? Explain in plain language for an analyst.", "What does median query time mean on the Fieldstone dashboard and how is it computed?", "Explain how active users is counted, for the week {n} dashboard review."],
    "support_assistant": ["A customer asks why their failed exports went up in week {n}. What do I tell them?", "Customer on tier {n} asks what median query time means on their dashboard. How do I answer?", "A customer wants to know how active users is counted on their dashboard. Reply please."],
}
def make_hard(per_feature=30, seed=7):
    rng = random.Random(seed); out = []
    for f in HARD:
        for i in range(per_feature):
            out.append({"id": f"{f[:3]}-{i:02d}", "feature": f, "user": rng.choice(USER[f]).format(n=rng.randint(2, 90)), "tokens": 1000})
    rng.shuffle(out); return out
def parse_hard(text):
    import re
    m = re.search(r'"feature"\s*:\s*"([a-z_]+)"', text or "")
    v = m.group(1) if m else next((n for n in HARD if n in (text or "")), "unparsed")
    return v if v in HARD or v == "unknown" else "unparsed"
