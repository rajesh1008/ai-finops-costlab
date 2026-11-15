from datetime import date
from costlab.claims import due, upcoming, CLAIMS
def test_nothing_due_on_check_day(): assert due(date(2026, 11, 11)) == []
def test_focus_claims_due_after_ratification():
    d = due(date(2026, 12, 4)); assert sum("FOCUS 1.5" in x[0] for x in d) == 3
def test_posting_claim_due_after_deadline(): assert any("postings" in x[0] for x in due(date(2026, 11, 14)))
def test_old_checks_flag_by_age(): assert len(due(date(2027, 1, 20))) == len(CLAIMS)
def test_upcoming_sorted(): u = upcoming(date(2026, 11, 11), 30); assert u == sorted(u) and len(u) >= 3
