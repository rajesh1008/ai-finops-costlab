"""Tests for the keyless lab modes: dated price table, local-model backend parsing/pricing, simulated backend."""
import pytest

from costlab import price_table as pt
from costlab.backends import local, simulated


def test_haiku45_list_prices_and_alias():
    p = pt.price_for("claude-haiku-4-5-20251001")
    assert (p.input, p.cache_write_5m, p.cache_write_1h, p.cache_read, p.output) == (1.0, 1.25, 2.0, 0.10, 5.0)


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        pt.price_for("claude-nonexistent")


def test_cost_lines_and_total():
    c = pt.cost_usd("claude-haiku-4-5", input_tokens=1_000_000, output_tokens=1_000_000,
                    cache_write_tokens=1_000_000, cache_read_tokens=1_000_000)
    assert c["input"] == pytest.approx(1.0) and c["output"] == pytest.approx(5.0)
    assert c["cache_write"] == pytest.approx(1.25) and c["cache_read"] == pytest.approx(0.10)
    assert c["total"] == pytest.approx(7.35)


def test_one_hour_write_and_batch_halves():
    c = pt.cost_usd("claude-sonnet-4-6", cache_write_tokens=1_000_000, write_ttl="1h", batch=True)
    assert c["total"] == pytest.approx(3.0)
    assert pt.cost_usd("claude-sonnet-4-6", input_tokens=10**6, batch=True)["total"] == pytest.approx(1.5)


def test_haiku55_long_prompt_tier_counts_cache_reads():
    short = pt.cost_usd("claude-haiku-5-5", input_tokens=100_000)
    long_ = pt.cost_usd("claude-haiku-5-5", input_tokens=1_000, cache_read_tokens=100_000)
    assert short["input"] == pytest.approx(0.01)
    assert long_["input"] == pytest.approx(1_000 * 0.50 / 1e6) and long_["cache_read"] == pytest.approx(0.005)


def test_bad_inputs():
    with pytest.raises(ValueError):
        pt.cost_usd("claude-haiku-4-5", input_tokens=-1)
    with pytest.raises(ValueError):
        pt.cost_usd("claude-haiku-4-5", write_ttl="10m")
    with pytest.raises(ValueError):
        pt.provenance("real-api", "claude-haiku-4-5")


def test_provenance_labels():
    d = pt.provenance("local-model", "claude-haiku-4-5", "qwen.gguf")
    assert d["mode"] == "local-model" and d["local_model"] == "qwen.gguf"
    assert d["pricing_date"] == "2026-11-16" and "Not an Anthropic invoice" in d["note"]
    assert simulated.provenance("claude-haiku-4-5")["mode"] == "simulated"


RESP_WARM = {"content": " Paris.", "tokens_predicted": 8, "tokens_evaluated": 28, "tokens_cached": 36,
             "timings": {"cache_n": 27, "prompt_n": 1, "prompt_ms": 50.0, "predicted_n": 8, "predicted_ms": 400.0}}
RESP_OLD = {"content": "x", "tokens_evaluated": 30, "timings": {"prompt_n": 10, "prompt_ms": 5.0, "predicted_n": 2, "predicted_ms": 9.0}}


def test_parse_completion_with_cache_n():
    c = local.parse_completion(RESP_WARM)
    assert (c["prompt_tokens"], c["cached_tokens"], c["evaluated_tokens"], c["output_tokens"]) == (28, 27, 1, 8)


def test_parse_completion_older_build():
    c = local.parse_completion(RESP_OLD)
    assert (c["prompt_tokens"], c["cached_tokens"], c["evaluated_tokens"]) == (30, 20, 10)


def test_price_local_mapping_read_write_input():
    counts = {"prompt_tokens": 1000, "cached_tokens": 0, "output_tokens": 10}
    cold = local.price_local(counts, "claude-haiku-4-5", prefix_tokens=900, cache_prefix="5m")
    assert cold["cache_write"] == pytest.approx(900 * 1.25 / 1e6) and cold["input"] == pytest.approx(100 / 1e6)
    warm = local.price_local({**counts, "cached_tokens": 900}, "claude-haiku-4-5", prefix_tokens=900, cache_prefix="5m")
    assert warm["cache_write"] == 0 and warm["cache_read"] == pytest.approx(900 * 0.1 / 1e6)
    assert warm["total"] < cold["total"]


def test_price_local_without_cache_request_is_all_input():
    c = local.price_local({"prompt_tokens": 1000, "cached_tokens": 900, "output_tokens": 0}, "claude-haiku-4-5")
    assert c["input"] == pytest.approx(1000 / 1e6) and c["cache_read"] == 0


def test_local_backend_rejects_unpriced_model():
    with pytest.raises(KeyError):
        local.LocalBackend(url="http://127.0.0.1:1", priced_as="gpt-x")


def test_local_backend_health_false_when_down():
    assert local.LocalBackend(url="http://127.0.0.1:1").health() is False


def test_simulated_session_ttl():
    r = simulated.simulate_session("claude-haiku-4-5", [1, 4, 6, 2], prefix_tokens=10_000, suffix_tokens=0,
                                   output_tokens=0, ttl="5m")
    assert (r["writes"], r["reads"]) == (2, 3)
    assert r["total_usd"] == pytest.approx((2 * 10_000 * 1.25 + 3 * 10_000 * 0.1) / 1e6)


def test_simulated_no_cache_and_gap_table():
    r = simulated.simulate_session("claude-haiku-4-5", [1] * 9, prefix_tokens=1000, suffix_tokens=0, output_tokens=0, ttl=None)
    assert r["total_usd"] == pytest.approx(10 * 1000 / 1e6)
    rows = simulated.breakeven_gap_table("claude-haiku-4-5", [2, 30, 120], prefix_tokens=20_000, suffix_tokens=200,
                                         output_tokens=300, calls=50)
    assert [r["cheapest"] for r in rows] == ["5m", "1h", "none"]
