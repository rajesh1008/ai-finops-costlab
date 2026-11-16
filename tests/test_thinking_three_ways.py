"""Offline tests for scripts/xai_reasoning_lab.py and for billing reasoning tokens as output (mocked, no key)."""
import importlib.util, pathlib
from unittest import mock

from costlab.backends import xai

spec = importlib.util.spec_from_file_location("xai_reasoning_lab",
                                              pathlib.Path(__file__).resolve().parents[1] / "scripts" / "xai_reasoning_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def test_extract_takes_last_answer_line():
    assert lab.extract("work\nANSWER: 12\nANSWER: **49.66**") == "49.66"
    assert lab.extract("no answer here") is None


def test_correct_numeric_text_and_signed():
    assert lab.correct("49.66", "49.66")
    assert lab.correct("$37,920", "37920")
    assert lab.correct("+0.2", "0.2") and lab.correct("-0.2", "0.2") is False
    assert lab.correct("Sunday", "Sunday") and not lab.correct("Tuesday", "Sunday")
    assert not lab.correct(None, "1")


def test_task_expectations_are_arithmetically_right():
    assert round(14500 * (1900 * 1.25 + 420 * 2.5) / 1e6, 2) == 49.66
    assert 48000 * 0.3 + 48000 * 0.7 * 0.7 == 37920
    assert round(20000 * (1.25 + 9 * 0.1) / 1e6, 5) == 0.043
    assert 0.8 * 0.002 + 0.2 * 0.012 == 0.004
    assert round(1 + 0.2 + 0.2 ** 2, 3) == 1.24
    cum, m = 0, 0
    while cum <= 600000:
        m += 1
        cum += 45000 * 1.06 ** (m - 1)
    assert m == 11


def test_reasoning_tokens_are_billed_as_output():
    resp = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 100,
                      "prompt_tokens_details": {"cached_tokens": 0},
                      "completion_tokens_details": {"reasoning_tokens": 900}}}
    b = xai.XaiBackend("grok-4.20-0309-reasoning", api_key="test")
    with mock.patch.object(b, "_request", return_value=resp):
        r = b.chat([{"role": "user", "content": "x"}])
    assert abs(r.cost_xai["total"] - (1000 * 1.25 + 1000 * 2.5) / 1e6) < 1e-9


def test_summarise_counts_by_arm():
    rows = [{"arm": "a", "correct": True, "completion_tokens": 5, "reasoning_tokens": 0, "wall_ms": 10.0,
             "cost_xai": {"total": 0.001}},
            {"arm": "a", "correct": False, "completion_tokens": 7, "reasoning_tokens": 0, "wall_ms": 20.0,
             "cost_xai": {"total": 0.002}}]
    s = lab.summarise(rows)["a"]
    assert s["tasks"] == 2 and s["correct"] == 1 and s["completion_tokens"] == 12 and s["usd_xai_total"] == 0.003
