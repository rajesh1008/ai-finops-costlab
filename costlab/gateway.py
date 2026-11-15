"""The Meter: a thin gateway that wraps every model call and writes one Cost Record per call.

Measured usage, estimated price and billed cost stay separate fields. Billed cost is
left empty here because the invoice, not the gateway, produces it.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .estimate import estimate_usd
from .records import CostRecord


class Meter:
    def __init__(self, client, log_path: Path, product: str, environment: str = "lab"):
        self.client = client
        self.log_path = Path(log_path)
        self.product = product
        self.environment = environment
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def call(self, *, model: str, session_id: str, step: int, feature: str,
             tenant: Optional[str] = None, team: Optional[str] = None, **kwargs):
        started = time.monotonic()
        msg = self.client.messages.create(model=model, **kwargs)
        latency_ms = int((time.monotonic() - started) * 1000)
        u = msg.usage
        cr = getattr(u, "cache_read_input_tokens", 0) or 0
        cw = getattr(u, "cache_creation_input_tokens", 0) or 0
        est = estimate_usd(f"anthropic:{model}", u.input_tokens, u.output_tokens, cr, cw)
        rec = CostRecord(
            record_id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc),
            vendor="anthropic", model=msg.model, product=self.product,
            feature=feature, team=team, tenant=tenant, environment=self.environment,
            input_tokens=u.input_tokens, output_tokens=u.output_tokens,
            cache_read_tokens=cr, cache_write_tokens=cw,
            estimated_cost_usd=round(est, 8), source="meter",
            notes=json.dumps({"session_id": session_id, "step": step,
                              "latency_ms": latency_ms, "stop_reason": msg.stop_reason}),
        )
        with self.log_path.open("a") as fh:
            fh.write(rec.model_dump_json() + "\n")
        return msg
