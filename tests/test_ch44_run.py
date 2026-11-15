import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch44_run_sims as s

def test_session_input_matches_measured_run():
    assert s.session_input(57, 117, 12) == 8406          # measured mean 8,411.3
    assert abs(s.session_input(57, 117, 12) - 8411.3) < 10

def test_session_input_grows_quadratically():
    assert s.session_input(57, 117, 40) == 93540 and s.session_input(57, 117, 80) == 374280

def test_measured_fold_saving():
    assert abs((1 - 4435.0 / 8411.3) - 0.4727) < 1e-3

def test_delayed_regression_break_even_lag():
    net, gross, loss = s.delayed_regression(900, 2400, 10, 22, 60)
    assert gross == 54000 and net > 0
    assert s.delayed_regression(900, 2400, 10, 23, 60)[0] < 0

def test_delayed_regression_values():
    assert s.delayed_regression(900, 2400, 10, 3, 60) == (46800, 54000, 7200)
    assert s.delayed_regression(900, 2400, 10, 30, 60) == (-18000, 54000, 72000)

def test_log_error():
    assert abs(s.log_error(60000, 120000) - 0.30103) < 1e-4 and abs(s.log_error(1_200_000, 120000) - 1.0) < 1e-9

def test_handoff_full_vs_summary():
    assert s.handoff_tokens(5, 3000, 600, "full") == 45000
    assert s.handoff_tokens(5, 3000, 600, "summary") == 17400
    assert s.handoff_tokens(8, 3000, 600, "full") == 108000

def test_forecast_buffer():
    g, proj, buf = s.forecast_buffer([41000, 44500, 47800, 53000, 56200, 61500], 3, 0.08)
    assert abs(g - 0.0846) < 1e-3 and round(proj) == 78466 and round(buf) == 88824

def test_record_storage():
    gb, usd = s.record_storage(2_000_000, 900, 395, 0.023)
    assert abs(gb - 711.0) < 1e-9 and abs(usd - 16.353) < 1e-9

def test_batch_breakeven_sign():
    assert abs(s.batch_breakeven(0.010, 0.5, 6, 0.0004) - 0.0026) < 1e-12
    assert s.batch_breakeven(0.010, 0.5, 6, 0.001) < 0

def test_autonomy_break_even_error_rate():
    auto, rev, be = s.autonomy_threshold(0.04, 25.0, 0.60, 0.85)
    assert abs(auto - 1.0) < 1e-12 and abs(rev - 0.75) < 1e-12 and abs(be - 0.60 / (0.85 * 25)) < 1e-12
    assert s.autonomy_threshold(0.01, 25.0, 0.60, 0.85)[0] < s.autonomy_threshold(0.01, 25.0, 0.60, 0.85)[1]

def test_outcome_price():
    assert s.outcome_price(0.18, 0.72, 0.6) == (0.25, 0.625)
    assert abs(s.outcome_price(0.18, 0.55, 0.6)[0] - 0.32727272727) < 1e-9

def test_body_storage():
    assert s.sampled_body_cost(5_000_000, 6000, 1.0, 30, 0.023)[0] == 900.0
    assert abs(s.sampled_body_cost(5_000_000, 6000, 0.02, 30, 0.023)[0] - 18.0) < 1e-9

def test_tokenizer_breakeven():
    ratio, be = s.tokenizer_breakeven(0.8, 1.339)
    assert ratio > 1 and abs(be - 0.7468) < 1e-3

def test_bucket_burst():
    assert s.bucket_burst(2.0, 120.0, 14.0, 30) == 10.0
    assert s.bucket_burst(2.0, 120.0, 2.0, 30) is None

def test_cap_share():
    costs = [4]*700 + [9]*200 + [25]*70 + [60]*25 + [210]*5
    assert s.cap_share(costs, 50) == (0.03, 1050, 8900) and s.cap_share(costs, 100) == (0.005, 550, 8900)

def test_value_breakeven_and_shadow():
    assert abs(s.value_breakeven(0.12, 0.6, 0.30) - 0.06) < 1e-12 and s.value_breakeven(0.12, 0.6, 0.15) < 0
    assert s.shadow_output_heavy(20000, 1800, 300, 1.0, 5.0, 4.0) == (66.0, 156.0)

def test_fold_net_and_break_even():
    plain = [762, 878, 994, 1109, 1225, 1341]; folded = [108, 224, 338, 447, 558, 668]
    saved, call, net = s.fold_net(plain, folded, 645, 80, 80, 51, 6)
    assert sum(plain) == 6309 and sum(folded) == 2343
    assert abs(call - 0.001045) < 1e-9 and abs(net - 0.002747) < 1e-6
    assert 1.8 < s.fold_break_even_turns(645, 80, 80) < 1.9

def test_fixed_cost_break_even():
    assert abs(s.fixed_cost_break_even(30000, 0.002, 2_500_000) - 6.0) < 1e-9
