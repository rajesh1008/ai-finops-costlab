from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CostRecord(BaseModel):
    """Measured usage, estimated price and billed cost stay distinct."""

    record_id: str
    occurred_at: datetime
    vendor: str
    model: str
    product: Optional[str] = None
    feature: Optional[str] = None
    team: Optional[str] = None
    tenant: Optional[str] = None
    environment: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    estimated_cost_usd: Optional[float] = None
    billed_cost_usd: Optional[float] = None
    source: str = Field(description="meter, invoice or smoke-test")
    notes: str = ""


class InvoiceLine(BaseModel):
    vendor: str
    description: str
    model: Optional[str] = None
    quantity: float
    unit: str
    amount_usd: float
    product_tag: Optional[str] = None
