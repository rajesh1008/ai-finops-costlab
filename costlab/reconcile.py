"""Reconcile a gateway log (the meter) to invoice lines within a stated tolerance (Chapter 5)."""
from dataclasses import dataclass


@dataclass
class Variance:
    key: str
    meter_usd: float
    invoice_usd: float

    @property
    def gap_usd(self) -> float:
        return self.invoice_usd - self.meter_usd

    @property
    def gap_pct(self) -> float:
        return self.gap_usd / self.invoice_usd if self.invoice_usd else 0.0


def reconcile(meter: dict[str, float], invoice: dict[str, float], tolerance: float = 0.02):
    keys = sorted(set(meter) | set(invoice))
    out = []
    for k in keys:
        v = Variance(k, meter.get(k, 0.0), invoice.get(k, 0.0))
        out.append((v, abs(v.gap_pct) <= tolerance))
    return out
