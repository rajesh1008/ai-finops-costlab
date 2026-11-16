"""Offline tests for scripts/xai_output_cap_lab.py (no key, no network)."""
import importlib.util, pathlib

spec = importlib.util.spec_from_file_location("xai_output_cap_lab",
                                              pathlib.Path(__file__).resolve().parents[1] / "scripts" / "xai_output_cap_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def row(cap, fin, toks, usd):
    return {"cap": cap, "finish_reason": fin, "completion_tokens": toks, "wall_ms": 100.0, "cost_xai": {"total": usd}}


def test_ten_questions_four_caps():
    assert len(lab.QUESTIONS) == 10 and lab.CAPS == [60, 150, 400, 1200]


def test_summarise_counts_cut_replies_as_spend():
    rows = [row(60, "length", 60, 0.0003), row(60, "length", 60, 0.0003), row(1200, "stop", 700, 0.002)]
    s = lab.summarise(rows)
    assert s["60"]["cut"] == 2 and s["60"]["complete"] == 0
    assert s["60"]["usd_spent_on_cut_replies"] == s["60"]["usd_xai_total"] == 0.0006
    assert s["1200"]["complete"] == 1 and s["1200"]["usd_spent_on_cut_replies"] == 0


def test_summarise_skips_errors():
    rows = [{"cap": 60, "error": "x"}, row(60, "stop", 30, 0.0001)]
    assert lab.summarise(rows)["60"]["calls"] == 1
