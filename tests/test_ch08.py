import json
from pathlib import Path
from costlab.focus import StrictCostRecord, upgrade_v1, to_focus_rows, token_total, check_no_double_count, try_validate, credential_id

RUNS = Path(__file__).resolve().parent.parent / "runs"


def _recs():
    return [StrictCostRecord(**upgrade_v1(json.loads(l)))
            for l in (RUNS / "cache-experiment-2026-11-10.jsonl").read_text().splitlines()]


def test_rows_sum_to_total():
    for r in _recs():
        assert check_no_double_count(to_focus_rows(r), token_total(r))


def test_double_counting_is_caught():
    r = next(x for x in _recs() if x.cache_read_tokens)
    bad = r.model_copy(update={"input_tokens": r.input_tokens + r.cache_read_tokens})
    assert not check_no_double_count(to_focus_rows(bad), token_total(r))


def test_unknown_field_refused_and_credential_not_secret():
    d = upgrade_v1(json.loads((RUNS / "cache-experiment-2026-11-10.jsonl").read_text().splitlines()[0]))
    d["prompt_tokens"] = 5
    assert not try_validate(d)[0]
    assert "sk-" not in credential_id("sk-test")


def test_rollup_equals_session_total_and_tail():
    from costlab.runs_graph import Call, rollup, session_costs, tail_summary
    t = [Call("a", "s", "r", None, 1.0), Call("b", "s", "k", "r", 2.0)]
    assert rollup(t)["r"] == session_costs(t)["s"] == 3.0
    s = tail_summary([1.0] * 97 + [100.0] * 3)
    assert s["top3pct_share"] > 0.7 and s["mean"] > s["median"]
