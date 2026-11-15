from costlab.stack import AnswerCostInputs, answer_cost
from costlab.thinking import thinking_gap, thinking_share


def test_thinking_gap_matches_lab_numbers():
    assert thinking_gap(392, 77) == 315
    assert thinking_gap(76, 80) == 0          # framing overhead never gives a negative gap
    assert abs(thinking_share(392, 77) - 315 / 392) < 1e-12


def test_human_line_is_in_the_total():
    i = AnswerCostInputs(0.004, 0.002, 0.0, 0.0, 0.0, review_rate=0.1, review_minutes=6, loaded_hourly_usd=60)
    r = answer_cost(i)
    assert abs(r["lines"]["human_review"] - 0.6) < 1e-12
    assert abs(sum(r["shares"].values()) - 1.0) < 1e-12
