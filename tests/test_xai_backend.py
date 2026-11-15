"""xai-api backend: mocked HTTP only, no key or network needed."""
import io
import json
import urllib.error

import pytest

from costlab.backends import xai
from costlab.backends.xai import XaiBackend, XaiError

RESP = {"id": "x", "model": "grok-4.20-0309-non-reasoning", "system_fingerprint": "fp_test",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 186, "completion_tokens": 1, "total_tokens": 187,
                  "prompt_tokens_details": {"text_tokens": 186, "cached_tokens": 128},
                  "completion_tokens_details": {"reasoning_tokens": 0},
                  "cost_in_usd_ticks": 1006000}}
MODELS = {"models": [{"id": "grok-4.20-0309-non-reasoning", "aliases": ["grok-4.20-non-reasoning"],
                      "prompt_text_token_price": 12500, "cached_prompt_text_token_price": 2000,
                      "completion_text_token_price": 25000, "prompt_text_token_price_long_context": 25000,
                      "cached_prompt_text_token_price_long_context": 4000,
                      "completion_text_token_price_long_context": 50000, "long_context_threshold": 200000}]}


class FakeOpener:
    def __init__(self, body=None, error=None):
        self.body, self.error, self.requests = body, error, []

    def __call__(self, req, timeout=None):
        self.requests.append((req, timeout))
        if self.error:
            raise self.error
        return io.BytesIO(json.dumps(self.body).encode())


def test_parse_usage_reads_cached_reasoning_and_ticks():
    c = xai.parse_usage(RESP)
    assert (c["prompt_tokens"], c["cached_tokens"], c["uncached_tokens"]) == (186, 128, 58)
    assert c["completion_tokens"] == 1 and c["reasoning_tokens"] == 0
    assert c["xai_reported_usd"] == pytest.approx(1006000e-10)


def test_parse_usage_tolerates_missing_details():
    c = xai.parse_usage({"choices": [{"message": {"content": "hi"}}], "usage": {"prompt_tokens": 10}})
    assert c["cached_tokens"] == 0 and c["reasoning_tokens"] == 0 and c["xai_reported_usd"] is None


def test_cost_matches_xai_reported_ticks():
    cost = xai.xai_cost_usd("grok-4.20-0309-non-reasoning", prompt_tokens=186, cached_tokens=128,
                            completion_tokens=1)
    assert cost["total"] == pytest.approx(1006000e-10)
    assert cost["long_context_rate"] is False


def test_long_context_rate_applies_to_all_tokens():
    cost = xai.xai_cost_usd("grok-4.3", prompt_tokens=200_000, cached_tokens=100_000, completion_tokens=1000)
    assert cost["long_context_rate"] is True
    assert cost["total"] == pytest.approx(100_000 * 2.5e-6 + 100_000 * 0.4e-6 + 1000 * 5e-6)


def test_cost_rejects_bad_counts():
    with pytest.raises(ValueError):
        xai.xai_cost_usd("grok-4.3", prompt_tokens=10, cached_tokens=11)


def test_models_entry_units_convert_to_per_million():
    p = xai.price_from_models_entry(MODELS["models"][0])
    assert p == xai.XAI_PRICES["grok-4.20-0309-non-reasoning"]


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        xai.xai_price_for("grok-0")


def test_chat_sends_conv_id_and_records_costs():
    op = FakeOpener(RESP)
    b = XaiBackend(api_key="test-key", opener=op, as_if_anthropic_model="claude-haiku-4-5")
    r = b.chat([{"role": "user", "content": "Say OK"}], max_tokens=5, conv_id="conv-1")
    req, timeout = op.requests[0]
    assert req.full_url.endswith("/chat/completions") and req.get_header("X-grok-conv-id") == "conv-1"
    assert json.loads(req.data)["model"] == "grok-4.20-0309-non-reasoning"
    assert timeout == 60.0
    assert r.cost_xai["total"] == pytest.approx(r.xai_reported_usd)
    # as-if Anthropic: 58 input at $1, 128 cache read at $0.10, 1 output at $5 per million
    assert r.cost_as_if_anthropic["total"] == pytest.approx(58e-6 + 128 * 0.1e-6 + 5e-6)
    assert r.wall_ms >= 0


def test_no_conv_id_header_when_not_given():
    op = FakeOpener(RESP)
    XaiBackend(api_key="k", opener=op).chat([{"role": "user", "content": "x"}])
    assert op.requests[0][0].get_header("X-grok-conv-id") is None


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(XaiError, match="XAI_API_KEY is not set"):
        XaiBackend(opener=FakeOpener(RESP)).chat([{"role": "user", "content": "x"}])


def test_http_error_message_does_not_leak_key():
    err = urllib.error.HTTPError("u", 403, "Forbidden", {}, io.BytesIO(b'{"error":"no credits"}'))
    b = XaiBackend(api_key="secret-value", opener=FakeOpener(error=err))
    with pytest.raises(XaiError) as e:
        b.chat([{"role": "user", "content": "x"}])
    assert "HTTP 403" in str(e.value) and "secret-value" not in str(e.value)


def test_network_error_wrapped():
    b = XaiBackend(api_key="k", opener=FakeOpener(error=urllib.error.URLError("timed out")))
    with pytest.raises(XaiError, match="network error"):
        b.chat([{"role": "user", "content": "x"}])


def test_live_price_from_models_endpoint_matches_table():
    b = XaiBackend(api_key="k", opener=FakeOpener(MODELS))
    assert b.live_price() == xai.XAI_PRICES["grok-4.20-0309-non-reasoning"]


def test_provenance_labels_mode_and_never_claims_anthropic():
    p = XaiBackend(api_key="key-must-not-appear", as_if_anthropic_model="claude-haiku-4-5").provenance()
    assert p["mode"] == "xai-api" and p["pricing_date"] == "2026-11-16"
    assert "Not a Claude call" in p["note"]
    assert "not a measurement" in p["as_if_anthropic"]["note"]
    assert "key-must-not-appear" not in json.dumps(p)


def _scan():
    import importlib.util, pathlib
    p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "secret_scan.py"
    spec = importlib.util.spec_from_file_location("secret_scan", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_secret_scan_catches_xai_and_anthropic_patterns():
    s = _scan()
    fake_xai = "xai-" + "A1b2C3d4" * 5
    fake_ant = "sk-" + "ant-" + "abcDEF123456" * 3
    assert s.scan_text("f", f"key = {fake_xai}") == ["f:1: xai-key"]
    assert "f:1: anthropic-key" in s.scan_text("f", fake_ant)
    assert s.scan_text("f", "XAI_API_KEY=" + "Zq9" * 8) == ["f:1: key-assignment"]


def test_secret_scan_allows_placeholders():
    s = _scan()
    assert s.scan_text(".env.example", "XAI_API_KEY=your-xai-key-here") == []
    assert s.scan_text(".gitignore", ".sec" + "rets/") == []
