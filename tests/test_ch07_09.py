from costlab.waste import simulate_retries, tool_overhead, human_wait_cost
from costlab.views import generate, finance_view, board_view, daily, invoice_view_daily


def test_cap_one_has_no_waste_but_fewer_outcomes():
    a = simulate_retries(0.2, 1); b = simulate_retries(0.2, 3)
    assert a.waste_share == 0 and b.outcomes > a.outcomes and b.waste_share > 0


def test_tool_overhead_scales_with_registry():
    assert tool_overhead(128, 120, 10)["session_tokens"] > 10 * tool_overhead(5, 120, 10)["session_tokens"] / 1.5


def test_human_wait_expiry_costs_more():
    assert human_wait_cost(20000, [10, 10])["cost"] > human_wait_cost(20000, [1, 1])["cost"]
    assert human_wait_cost(20000, [1, 1])["expired"] == 0


def test_views_share_one_total():
    rows = generate(days=5, per_day=50)
    assert abs(finance_view(rows)["total"] - sum(v[0] for v in board_view(rows).values())) < 1e-9
    assert abs(sum(invoice_view_daily(rows, 5).values()) - sum(daily(rows).values())) < 1e-9


def test_otel_conversion():
    import pytest
    from costlab.views import otel_to_cr2
    assert otel_to_cr2(21800, 20000, 0) == 1800
    with pytest.raises(ValueError):
        otel_to_cr2(1000, 900, 300)


def test_anomaly_cap_and_median():
    from costlab.views import generate, daily, top_sessions
    from costlab.anomaly import trailing_median_alert, session_cap_stop
    rows = generate(days=25, per_day=60, spike_day=19)
    sid, cost = top_sessions(rows, 1)[0]
    step, spent = session_cap_stop(rows, sid, 0.10)
    assert step is not None and spent < cost / 5
    assert 19 in trailing_median_alert(daily(rows), pct=0.25)
