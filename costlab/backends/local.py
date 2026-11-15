"""Local-model backend: a llama.cpp `llama-server` on 127.0.0.1 (OpenAI-compatible plus native /completion).

Measures real token counts, latency and llama.cpp prefix-cache reuse (`tokens_cached`, `cache_prompt`),
then prices the tokens at a chosen Anthropic model's published list prices (costlab.price_table).

Mapping (stated in every output):
  * prompt tokens served from the local KV prefix cache  -> priced as Anthropic cache reads
  * if `cache_prefix` is set, the uncached part of the declared prefix -> priced as a cache write (5m or 1h)
  * all other prompt tokens -> base input; generated tokens -> output
Token counts come from the local model's tokenizer, not Claude's; they are an analogue, not a Claude count.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass, asdict, field

from costlab import price_table

DEFAULT_URL = os.environ.get("COSTLAB_LOCAL_URL", "http://127.0.0.1:8088")


@dataclass
class LocalResult:
    text: str
    prompt_tokens: int
    cached_tokens: int
    evaluated_tokens: int
    output_tokens: int
    prompt_ms: float
    gen_ms: float
    wall_ms: float
    priced: dict = field(default_factory=dict)

    def as_dict(self):
        return asdict(self)


def _post(url, payload, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def parse_completion(resp: dict) -> dict:
    """Normalise a llama.cpp /completion response into token and timing counts."""
    t = resp.get("timings") or {}
    evaluated = int(t.get("prompt_n", resp.get("tokens_evaluated", 0)))
    cached = int(resp.get("tokens_cached", 0)) if "timings" not in resp else int(t.get("cache_n", 0))
    if "timings" in resp and "cache_n" not in t:
        # older builds: tokens_evaluated is the full prompt, prompt_n only the newly evaluated part
        total = int(resp.get("tokens_evaluated", evaluated))
        cached = max(0, total - evaluated)
    prompt_total = cached + evaluated
    return {"text": resp.get("content", ""), "prompt_tokens": prompt_total, "cached_tokens": cached,
            "evaluated_tokens": evaluated, "output_tokens": int(t.get("predicted_n", resp.get("tokens_predicted", 0))),
            "prompt_ms": float(t.get("prompt_ms", 0.0)), "gen_ms": float(t.get("predicted_ms", 0.0))}


def price_local(counts: dict, priced_as: str, *, prefix_tokens: int = 0, cache_prefix: str | None = None,
                batch: bool = False) -> dict:
    """Price measured local counts at Anthropic list prices using the mapping in the module docstring."""
    cached = counts["cached_tokens"]
    write = max(0, min(prefix_tokens, counts["prompt_tokens"]) - cached) if cache_prefix else 0
    uncached = counts["prompt_tokens"] - cached - write
    if not cache_prefix:
        # without a cache request Anthropic would bill the whole prompt as base input
        uncached, cached = counts["prompt_tokens"], 0
    return price_table.cost_usd(priced_as, input_tokens=uncached, output_tokens=counts["output_tokens"],
                                cache_write_tokens=write, cache_read_tokens=cached,
                                write_ttl=cache_prefix or "5m", batch=batch)


class LocalBackend:
    def __init__(self, url: str = DEFAULT_URL, priced_as: str = "claude-haiku-4-5"):
        self.url = url.rstrip("/")
        self.priced_as = priced_as
        price_table.price_for(priced_as)

    def model_name(self) -> str:
        try:
            d = _get(self.url + "/v1/models")
            return os.path.basename(d["data"][0]["id"])
        except Exception:
            return "unknown"

    def health(self) -> bool:
        try:
            return _get(self.url + "/health").get("status") == "ok"
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        return len(_post(self.url + "/tokenize", {"content": text})["tokens"])

    def complete(self, prefix: str, suffix: str, *, max_tokens: int = 32, cache_prefix: str | None = "5m",
                 batch: bool = False, temperature: float = 0.0) -> LocalResult:
        """One call. `prefix` is the stable part (system prompt, documents), `suffix` the varying question."""
        prompt = prefix + suffix
        t0 = time.perf_counter()
        resp = _post(self.url + "/completion", {"prompt": prompt, "n_predict": max_tokens, "cache_prompt": True,
                                                "temperature": temperature, "seed": 7})
        wall = (time.perf_counter() - t0) * 1000
        c = parse_completion(resp)
        prefix_tokens = self.count_tokens(prefix) if cache_prefix else 0
        priced = price_local(c, self.priced_as, prefix_tokens=prefix_tokens, cache_prefix=cache_prefix, batch=batch)
        return LocalResult(wall_ms=wall, priced=priced, **c)

    def provenance(self) -> dict:
        return price_table.provenance("local-model", self.priced_as, self.model_name())
