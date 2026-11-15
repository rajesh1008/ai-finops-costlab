"""Outcome contracts (Chapter 4) and cost per outcome under two denominators.

An outcome contract is a signed definition. It is data, so a missing field is a failed check
and not a matter of opinion. The measurement helpers take counts the caller supplies; nothing
here invents a count.
"""
from dataclasses import dataclass, field

REQUIRED = ("product", "outcome_statement", "counted_event", "quality_bar", "evidence_source",
            "exclusions", "owner", "signed_on", "value_tier")


@dataclass
class OutcomeContract:
    product: str
    outcome_statement: str = ""
    counted_event: str = ""      # the record that is counted, with the system that writes it
    quality_bar: str = ""        # the check an outcome must pass to be counted
    evidence_source: str = ""    # where a third party could verify the count
    exclusions: str = ""         # what is explicitly not an outcome
    owner: str = ""              # the person who signs
    signed_on: str = ""
    value_tier: str = ""         # avoided cost, saved time, revenue protected, revenue created, none stated

    def missing(self) -> list[str]:
        return [f for f in REQUIRED if not getattr(self, f)]

    def is_valid(self) -> bool:
        return not self.missing()


@dataclass
class Window:
    cost_usd: float
    emitted: int          # responses the model produced (what an API log can count)
    accepted: int         # responses that passed the quality bar
    benefited: int        # accepted responses where the user's task stayed done (for example no recontact in seven days)


def cost_per(cost_usd: float, n: int) -> float:
    if n <= 0:
        raise ValueError("denominator is zero: a cost without a denominator is a rumour")
    return cost_usd / n


def three_denominators(w: Window) -> dict:
    return {
        "per_emitted": cost_per(w.cost_usd, w.emitted),
        "per_accepted": cost_per(w.cost_usd, w.accepted),
        "per_benefited": cost_per(w.cost_usd, w.benefited),
        "accept_rate": w.accepted / w.emitted,
        "benefit_rate": w.benefited / w.emitted,
    }
