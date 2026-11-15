"""Tags that survive (Chapter 5).

Product, team and environment come from the credential's registry entry, never from a header the
caller sets. A caller may supply only allow-listed attribution keys (feature, tenant), and unknown
keys are rejected, not ignored. A call whose credential is not in the registry is recorded with
product 'unregistered' so it shows up in reports instead of vanishing.
"""
from dataclasses import dataclass

CALLER_ALLOWED = {"feature", "tenant"}


@dataclass(frozen=True)
class Credential:
    key_id: str
    product: str
    team: str
    environment: str


def resolve_tags(key_id: str, caller_tags: dict, registry: dict[str, Credential]) -> dict:
    unknown = set(caller_tags) - CALLER_ALLOWED
    if unknown:
        raise ValueError(f"caller tried to set non-allowed tags: {sorted(unknown)}")
    cred = registry.get(key_id)
    if cred is None:
        return {"product": "unregistered", "team": None, "environment": None, **caller_tags}
    return {"product": cred.product, "team": cred.team, "environment": cred.environment, **caller_tags}
