"""Chapter 8: a typed, versioned cost record and a mapping to FOCUS 1.5 working-draft shapes.

The mapping follows the FOCUS 1.5 release-scope page (inspected 10 November 2026): AI token
attributes live as recommended properties inside SkuPriceDetails (ModelId, TokenDirection,
TokenCacheAction), one row per token class, a cached token counted on one row only.
1.5 is a working draft until ratification on 3 December 2026, so these names are provisional.
"""
import hashlib
import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, ValidationError

SCHEMA_VERSION = "cr-2"


class StrictCostRecord(BaseModel):
    """Version 2 of the Cost Record. Unknown fields are refused, a version is required."""
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    record_id: str
    occurred_at: datetime
    vendor: str
    model: str
    credential_id: str
    product: Optional[str] = None
    feature: Optional[str] = None
    tenant: Optional[str] = None
    input_tokens: int = Field(ge=0)          # uncached input only
    output_tokens: int = Field(ge=0)         # includes thinking tokens when billed as output
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    estimated_cost_usd: Optional[float] = None
    billed_cost_usd: Optional[float] = None


def credential_id(secret_label: str) -> str:
    """An identifier derived from a label, never the key itself."""
    return "cred-" + hashlib.sha256(secret_label.encode()).hexdigest()[:10]


def upgrade_v1(d: dict, cred_label: str = "lab-key") -> dict:
    """Version 1 (no schema_version, no credential) to version 2. Drops the free-text notes."""
    keep = {k: d.get(k) for k in (
        "record_id", "occurred_at", "vendor", "model", "product", "feature", "tenant",
        "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
        "estimated_cost_usd", "billed_cost_usd")}
    keep["schema_version"] = SCHEMA_VERSION
    keep["credential_id"] = credential_id(cred_label)
    return keep


_CLASSES = (
    ("input_tokens", "Input", "Uncached"),
    ("cache_write_tokens", "Input", "Write"),
    ("cache_read_tokens", "Input", "Read"),
    ("output_tokens", "Output", "Uncached"),
)


def to_focus_rows(rec: StrictCostRecord) -> list[dict]:
    """One row per non-empty token class. Cost columns are left empty: the meter measures usage."""
    rows = []
    for field, direction, action in _CLASSES:
        qty = getattr(rec, field)
        if qty == 0:
            continue
        rows.append({
            "ChargePeriodStart": rec.occurred_at.isoformat(),
            "ServiceProviderName": rec.vendor,
            "ConsumedQuantity": qty,
            "ConsumedUnit": "Tokens",
            "SkuMeter": f"{direction} tokens" + ("" if action == "Uncached" else f" ({action.lower()})"),
            "SkuPriceDetails": json.dumps({"ModelId": rec.model, "TokenDirection": direction,
                                           "TokenCacheAction": action}, sort_keys=True),
            "CredentialId": rec.credential_id,
            "x_RecordId": rec.record_id,
            "x_Product": rec.product, "x_Feature": rec.feature, "x_Tenant": rec.tenant,
        })
    return rows


def token_total(rec: StrictCostRecord) -> int:
    return (rec.input_tokens + rec.output_tokens + rec.cache_read_tokens + rec.cache_write_tokens)


def check_no_double_count(rows: list[dict], provider_total: int) -> bool:
    """Rows must sum to the provider's own total, with each cached token on one row only."""
    return sum(r["ConsumedQuantity"] for r in rows) == provider_total


def try_validate(d: dict) -> tuple[bool, str]:
    try:
        StrictCostRecord(**d)
        return True, "ok"
    except ValidationError as e:
        first = e.errors()[0]
        return False, f"{first['type']} on {'.'.join(str(x) for x in first['loc'])}"
