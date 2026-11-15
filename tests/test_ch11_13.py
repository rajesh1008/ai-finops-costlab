from costlab.cpst import simulate, report
from costlab.margin import customers, summary, seat_price, per_task
from costlab.forecast import history, trend_forecast, driver_forecast, mape


def test_cpst_includes_failures():
    t, r = simulate(n=800)
    rep = report(t, r, False)
    assert rep["cpst"] > rep["mean_cost_of_successes"]


def test_machine_only_cpst_rises_with_cap_but_human_included_falls():
    a = report(*simulate(retry_cap=1), True)["cpst"], report(*simulate(retry_cap=1), False)["cpst"]
    b = report(*simulate(retry_cap=4), True)["cpst"], report(*simulate(retry_cap=4), False)["cpst"]
    assert b[0] < a[0] and b[1] > a[1]


def test_flat_seat_has_negative_customers():
    cs = customers()
    assert summary(cs, seat_price)["neg_share"] > 0.1 and summary(cs, per_task)["neg_share"] == 0


def test_forecast_error_shrinks_when_told_about_event():
    h = history()
    a = [x["spend"] for x in h if 12 <= x["m"] <= 14]
    naive = mape(driver_forecast(h, 11, 3, 0.07, 0.03), a)
    told = mape(driver_forecast(h, 11, 3, 0.07, 0.03, {13: -0.35}), a)
    assert told < naive
