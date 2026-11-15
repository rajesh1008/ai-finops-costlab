"""Chapter 32: cost policy as code. A pure decision function over a request description and a rule set, in the shape the Chapter 26 Authority and the
published gateway designs use: gather state outside, decide here, perform effects outside. Rules are data. Two modes per rule: shadow (decision recorded, request allowed) and enforce.
Prices come from costlab.prices (dated placeholders). No network, no clock inside the decision."""
from dataclasses import dataclass, field
from .prices import PLACEHOLDER_USD_PER_MTIOK

def worst_case_usd(model, input_tokens, max_tokens):
    t = PLACEHOLDER_USD_PER_MTIOK.get("anthropic:" + model)
    if t is None: return None
    return input_tokens / 1e6 * t["input"] + max_tokens / 1e6 * t["output"]

@dataclass
class Request:
    model: str; input_tokens: int; max_tokens: int
    team: str = ""; purpose: str = ""; tier: str = "prod"; month_spend_team: float = 0.0; extra: dict = field(default_factory=dict)

@dataclass
class Rule:
    id: str; kind: str; params: dict; mode: str = "enforce"   # kinds: model_allowlist, required_tags, price_ceiling, max_tokens_ceiling, legacy_model, team_month_cap

@dataclass
class Decision:
    allowed: bool; would_deny: list; denied_by: list     # would_deny: ids of rules that fire (enforce or shadow); denied_by: ids of enforcing rules that fire

def _fires(rule, r):
    p = rule.params
    if rule.kind == "model_allowlist":
        return r.model not in p["allowed"]
    if rule.kind == "required_tags":
        return any(not getattr(r, k) for k in p["tags"])
    if rule.kind == "price_ceiling":
        w = worst_case_usd(r.model, r.input_tokens, r.max_tokens)
        return w is None or w > p["usd"]
    if rule.kind == "max_tokens_ceiling":
        return r.max_tokens > p["max_tokens"]
    if rule.kind == "legacy_model":
        return r.model in p["models"] and r.purpose not in p["exempt_purposes"]
    if rule.kind == "team_month_cap":
        w = worst_case_usd(r.model, r.input_tokens, r.max_tokens) or 0.0
        return r.month_spend_team + w > p["usd"]
    raise ValueError(f"unknown rule kind {rule.kind}")

@dataclass
class Exemption:
    rule_id: str; team: str; purpose: str; expires: str; approver: str   # expires is an ISO date; compared as a string against `today`

def exempt(x, r, today):
    return x.team == r.team and x.purpose == r.purpose and today <= x.expires

def decide(r, rules, exemptions=(), today="0000-00-00"):
    """Default is deny for an unknown model or an unpriced one (price_ceiling fires when the price is unknown). Rules are independent; all that fire are listed.
    An exemption lifts one rule for one team and purpose until its expiry date; `today` is passed in because a decision function reads no clock."""
    fired = [x for x in rules if _fires(x, r)]
    lifted = {e.rule_id for e in exemptions if exempt(e, r, today)}
    enforcing = [x.id for x in fired if x.mode == "enforce" and x.id not in lifted]
    return Decision(allowed=not enforcing, would_deny=[x.id for x in fired], denied_by=enforcing)

MESSAGES = {
    "model_allowlist": "Model {model} is not approved for this account. Approved models are listed in the policy; ask the platform team to add it.",
    "required_tags": "The request has no team or purpose tag. Add both headers and retry; untagged spend is refused so that it has an owner.",
    "price_ceiling": "The worst-case cost of this request ({est}) is above the ceiling for its class. Lower max_tokens or shorten the input, or request an exemption.",
    "max_tokens_ceiling": "max_tokens {max_tokens} is above the ceiling for this class. Lower it, or request an exemption.",
    "legacy_model": "Model {model} is scheduled for retirement and is closed to new purposes. Use the named successor.",
    "team_month_cap": "The team's monthly allowance would be exceeded. The owner has been notified; see the budget page.",
}

def refusal_message(rule, r):
    est = worst_case_usd(r.model, r.input_tokens, r.max_tokens)
    return MESSAGES[rule.kind].format(model=r.model, max_tokens=r.max_tokens, est="unpriced" if est is None else f"${est:.5f}") + f" [rule {rule.id}]"

def replay(requests, rules):
    """Run every request through the rules. Returns per-rule counts of firings (shadow and enforce), and the totals."""
    per = {x.id: {"fires": 0, "blocks": 0} for x in rules}; blocked = 0
    out = []
    for r in requests:
        d = decide(r, rules); out.append(d)
        for i in d.would_deny: per[i]["fires"] += 1
        for i in d.denied_by: per[i]["blocks"] += 1
        blocked += (not d.allowed)
    return {"per_rule": per, "blocked": blocked, "n": len(requests), "decisions": out}
