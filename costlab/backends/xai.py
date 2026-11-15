"""xAI (Grok) API backend: real calls to xAI's OpenAI-compatible Chat Completions endpoint.

Mode `xai-api`. Everything this backend records is measured on xAI's Grok API and priced at xAI's own
list prices. It is NOT a Claude call and NOT an Anthropic invoice figure. An optional `as_if_anthropic`
line re-prices the same token counts at Anthropic list prices (costlab.price_table) for comparison only;
it must always be labelled as a calculation.

What is recorded per call (from the response `usage` object):
  * prompt_tokens, cached_tokens (usage.prompt_tokens_details.cached_tokens), uncached = prompt - cached
  * completion_tokens, reasoning_tokens (usage.completion_tokens_details.reasoning_tokens)
  * cost_in_usd_ticks if xAI returns it (1 tick = 1e-10 USD), plus our own line-item cost at list prices
  * wall-clock latency in milliseconds

xAI price units. GET /v1/models returns prices as integers per token in units of 1e-10 USD
(for example prompt_text_token_price 12500 = $1.25 per million tokens). This matches the per-million
table on https://docs.x.ai/docs/models, read 16 Nov 2026. Prompts at or above `long_context_threshold`
(200,000 tokens) are billed at the long-context rate for all tokens in the request.

xAI caches matching prompt prefixes automatically. The `x-grok-conv-id` header routes requests with the
same id to the same server, which makes cache hits likelier but never certain
(https://docs.x.ai/developers/advanced-api-usage/prompt-caching).

The key is read only from the XAI_API_KEY environment variable and is never logged or written out.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date

from costlab import price_table

API_BASE = os.environ.get("COSTLAB_XAI_URL", "https://api.x.ai/v1")
PRICING_DATE = date(2026, 11, 16)
PRICING_SOURCE = "https://docs.x.ai/docs/models (and GET https://api.x.ai/v1/models)"
UNIT_USD = 1e-10          # xAI integer price unit and cost tick, in USD
DEFAULT_MODEL = "grok-4.20-0309-non-reasoning"


@dataclass(frozen=True)
class XaiPrice:
    """USD per million tokens."""
    input: float
    cached_input: float
    output: float
    long_threshold: int = 200_000
    long_input: float | None = None
    long_cached_input: float | None = None
    long_output: float | None = None


# Read 16 Nov 2026 from https://docs.x.ai/docs/models; identical to the /v1/models integers / 10,000.
XAI_PRICES: dict[str, XaiPrice] = {
    "grok-4.20-0309-non-reasoning": XaiPrice(1.25, 0.20, 2.50, 200_000, 2.50, 0.40, 5.00),
    "grok-4.20-0309-reasoning": XaiPrice(1.25, 0.20, 2.50, 200_000, 2.50, 0.40, 5.00),
    "grok-4.3": XaiPrice(1.25, 0.20, 2.50, 200_000, 2.50, 0.40, 5.00),
    "grok-4.5": XaiPrice(2.00, 0.30, 6.00, 200_000, 4.00, 0.60, 12.00),
    "grok-4.6": XaiPrice(2.00, 0.50, 6.00, 200_000, 4.00, 1.00, 12.00),
    "grok-4.7": XaiPrice(2.00, 0.50, 6.00, 200_000, 4.00, 1.00, 12.00),
    "grok-build-0.1": XaiPrice(1.00, 0.20, 2.00, 200_000, 2.00, 0.40, 4.00),
}
XAI_ALIASES = {"grok-4.20-non-reasoning": "grok-4.20-0309-non-reasoning",
               "grok-4.20-non-reasoning-latest": "grok-4.20-0309-non-reasoning",
               "grok-4.20": "grok-4.20-0309-reasoning", "grok-4.20-reasoning": "grok-4.20-0309-reasoning"}


def price_from_models_entry(entry: dict) -> XaiPrice:
    """Convert one /v1/models (or /v1/language-models) entry's integer prices to USD per million tokens."""
    per_m = lambda k: entry[k] * UNIT_USD * 1e6 if entry.get(k) is not None else None  # noqa: E731
    return XaiPrice(per_m("prompt_text_token_price"), per_m("cached_prompt_text_token_price"),
                    per_m("completion_text_token_price"), int(entry.get("long_context_threshold", 200_000)),
                    per_m("prompt_text_token_price_long_context"),
                    per_m("cached_prompt_text_token_price_long_context"),
                    per_m("completion_text_token_price_long_context"))


def xai_price_for(model: str) -> XaiPrice:
    key = XAI_ALIASES.get(model, model)
    if key not in XAI_PRICES:
        raise KeyError(f"no dated xAI price for {model!r}; add it from {PRICING_SOURCE}")
    return XAI_PRICES[key]


def xai_cost_usd(model: str, *, prompt_tokens: int, cached_tokens: int = 0, completion_tokens: int = 0,
                 price: XaiPrice | None = None) -> dict:
    """Line-item cost at xAI list prices. Reasoning tokens are already inside completion_tokens."""
    if min(prompt_tokens, cached_tokens, completion_tokens) < 0 or cached_tokens > prompt_tokens:
        raise ValueError("token counts must be non-negative and cached_tokens <= prompt_tokens")
    p = price or xai_price_for(model)
    long = prompt_tokens >= p.long_threshold and p.long_input is not None
    pi, pc, po = (p.long_input, p.long_cached_input, p.long_output) if long else (p.input, p.cached_input, p.output)
    lines = {"input": (prompt_tokens - cached_tokens) * pi / 1e6,
             "cached_input": cached_tokens * pc / 1e6,
             "output": completion_tokens * po / 1e6}
    lines["total"] = sum(lines.values())
    lines["long_context_rate"] = long
    return lines


def parse_usage(resp: dict) -> dict:
    """Normalise a Chat Completions response's usage block."""
    u = resp.get("usage") or {}
    pd = u.get("prompt_tokens_details") or {}
    cd = u.get("completion_tokens_details") or {}
    prompt = int(u.get("prompt_tokens", 0))
    cached = int(pd.get("cached_tokens", 0) or 0)
    ticks = u.get("cost_in_usd_ticks")
    choice = (resp.get("choices") or [{}])[0]
    return {"text": (choice.get("message") or {}).get("content") or "",
            "finish_reason": choice.get("finish_reason"),
            "model": resp.get("model"), "system_fingerprint": resp.get("system_fingerprint"),
            "prompt_tokens": prompt, "cached_tokens": cached, "uncached_tokens": prompt - cached,
            "completion_tokens": int(u.get("completion_tokens", 0)),
            "reasoning_tokens": int(cd.get("reasoning_tokens", 0) or 0),
            "xai_reported_usd": ticks * UNIT_USD if isinstance(ticks, (int, float)) else None}


def as_if_anthropic(counts: dict, priced_as: str) -> dict:
    """Re-price xAI token counts at Anthropic list prices: cached -> cache read, rest -> input, completion -> output.
    A comparison calculation only (different tokenizer, different model); never an Anthropic measurement."""
    return price_table.cost_usd(priced_as, input_tokens=counts["uncached_tokens"],
                                cache_read_tokens=counts["cached_tokens"],
                                output_tokens=counts["completion_tokens"])


class XaiError(RuntimeError):
    pass


@dataclass
class XaiResult:
    text: str
    finish_reason: str | None
    model: str | None
    system_fingerprint: str | None
    prompt_tokens: int
    cached_tokens: int
    uncached_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    xai_reported_usd: float | None
    wall_ms: float
    cost_xai: dict = field(default_factory=dict)
    cost_as_if_anthropic: dict | None = None

    def as_dict(self):
        return asdict(self)


class XaiBackend:
    def __init__(self, model: str = DEFAULT_MODEL, *, api_key: str | None = None, base_url: str = API_BASE,
                 timeout: float = 60.0, as_if_anthropic_model: str | None = None, opener=None):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.as_if = as_if_anthropic_model
        self._key = api_key if api_key is not None else os.environ.get("XAI_API_KEY", "")
        self._open = opener or urllib.request.urlopen
        self.price = xai_price_for(model)
        if as_if_anthropic_model:
            price_table.price_for(as_if_anthropic_model)

    def _request(self, method: str, path: str, payload: dict | None = None, headers: dict | None = None) -> dict:
        if not self._key:
            raise XaiError("XAI_API_KEY is not set")
        h = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        h.update(headers or {})
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, headers=h, method=method)
        try:
            with self._open(req, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            raise XaiError(f"HTTP {e.code}: {body}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise XaiError(f"network error: {e}") from None

    def list_models(self) -> list[dict]:
        return self._request("GET", "/language-models").get("models", [])

    def live_price(self) -> XaiPrice | None:
        """Price for self.model read from the API now (None if not listed)."""
        for m in self.list_models():
            if m.get("id") == self.model or self.model in (m.get("aliases") or []):
                return price_from_models_entry(m)
        return None

    def chat(self, messages: list[dict], *, max_tokens: int = 32, temperature: float = 0.0,
             conv_id: str | None = None, **extra) -> XaiResult:
        payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                   "temperature": temperature, **extra}
        headers = {"x-grok-conv-id": conv_id} if conv_id else None
        t0 = time.perf_counter()
        resp = self._request("POST", "/chat/completions", payload, headers)
        wall = (time.perf_counter() - t0) * 1000
        c = parse_usage(resp)
        cost = xai_cost_usd(self.model, prompt_tokens=c["prompt_tokens"], cached_tokens=c["cached_tokens"],
                            completion_tokens=c["completion_tokens"], price=self.price)
        alt = as_if_anthropic(c, self.as_if) if self.as_if else None
        return XaiResult(wall_ms=wall, cost_xai=cost, cost_as_if_anthropic=alt, **c)

    def provenance(self) -> dict:
        d = {"mode": "xai-api", "model": self.model, "pricing": "xAI list prices",
             "pricing_date": PRICING_DATE.isoformat(), "pricing_source": PRICING_SOURCE,
             "note": ("Measured on xAI's Grok API (real calls); dollars at xAI's published list prices. "
                      "Not a Claude call and not an Anthropic invoice figure.")}
        if self.as_if:
            d["as_if_anthropic"] = {"priced_as": self.as_if, "pricing_date": price_table.PRICING_DATE.isoformat(),
                                    "pricing_source": price_table.PRICING_SOURCE,
                                    "note": ("Comparison only: the same xAI token counts re-priced at Anthropic list "
                                             "prices (cached -> cache read). A calculation, not a measurement.")}
        return d
