import random
from costlab.pricing import *

def test_no_leak_buyer_pays_list():
    r = billed_outcomes(5000, 0.5, 0.0, 0.0, random.Random(1))
    assert r["billed"] == r["true"]
    assert abs(buyer_price_per_true(0.99, r) - 0.99) < 1e-9

def test_leak_raises_billed_and_deduction_reduces():
    a = billed_outcomes(5000, 0.5, 0.2, 0.0, random.Random(1))
    b = billed_outcomes(5000, 0.5, 0.2, 0.5, random.Random(1))
    assert a["billed"] > a["true"] and b["billed"] < a["billed"] and b["deducted"] > 0

def test_breakeven():
    assert breakeven_resolution_rate(0.5, 1.0) == 0.5
    assert vendor_margin(100, 0.3, 1.0, 0.3) == 0.0 or abs(vendor_margin(100, 0.3, 1.0, 0.3)) < 1e-9

def test_triage_rules_label_and_miss():
    from costlab.triage import rule_label
    assert rule_label("How do I reset my password") == "password"
    assert rule_label("Is there a mobile app") is None
    assert rule_label("I cancelled my order but you still charged me on the invoice") == "shipping"  # known rule error, used in the chapter

def test_cascade_agreement_reads_bold_answer():
    from costlab.cascade import agree, correct
    a = "The net amount charged is **$1,185**, since the discounted total of $1,659 minus $474 leaves $1,185."
    b = "The net amount charged is **$1,185.00**. The 28 seats cost $2,212."
    assert agree(a, b) and correct(a, 1185.0)
    assert not agree(a, "The net is **$1,000**.")
