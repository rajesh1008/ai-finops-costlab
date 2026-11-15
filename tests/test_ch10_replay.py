import numpy as np
from costlab.alertreplay import *
def test_month_shapes_and_incident_raises_spend():
    pool = [1.0, 1.0, 1.0, 1.0, 10.0]; tail = [10.0]
    a, h = month(pool, tail, seed=1); b, _ = month(pool, tail, inc_start=360, inc_extra=0.5, seed=1)
    assert a.shape == (720,) and b[360:].sum() > a[360:].sum()
def test_rules_return_none_on_flat_series():
    s = np.full(720, 100.0); assert first_hour_alert_hourly(s) is None and first_day_alert_trailing_median(s.reshape(-1, 24).sum(1)) is None
def test_hourly_rule_fires_on_step():
    s = np.full(720, 100.0); s[500:] = 200.0; assert first_hour_alert_hourly(s, start=480) == 500
def test_hot_rule_start():
    h = np.zeros(100, dtype=int); h[10] = 9; h[50] = 9; assert first_hour_alert_hot(h, 8) == 10 and first_hour_alert_hot(h, 8, start=20) == 50
