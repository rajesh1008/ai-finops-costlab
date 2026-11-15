import json
from types import SimpleNamespace
from costlab.gateway import Meter


class FakeMessages:
    def create(self, **kw):
        usage = SimpleNamespace(input_tokens=100, output_tokens=50,
                                cache_read_input_tokens=1000, cache_creation_input_tokens=0)
        return SimpleNamespace(usage=usage, model=kw["model"], stop_reason="end_turn", content=[])


def test_meter_writes_one_record_per_call(tmp_path):
    client = SimpleNamespace(messages=FakeMessages())
    log = tmp_path / "m.jsonl"
    meter = Meter(client, log, product="support-agent")
    meter.call(model="claude-haiku-4-5-20251001", session_id="s1", step=1, feature="chat", max_tokens=10)
    meter.call(model="claude-haiku-4-5-20251001", session_id="s1", step=2, feature="chat", max_tokens=10)
    rows = [json.loads(x) for x in log.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["cache_read_tokens"] == 1000
    assert rows[0]["billed_cost_usd"] is None
    # 100*1.00 + 50*5.00 + 1000*0.10 = 450 per million tokens-dollars -> 0.00045
    assert abs(rows[0]["estimated_cost_usd"] - 0.00045) < 1e-9
    assert json.loads(rows[1]["notes"])["step"] == 2


def test_cache_read_is_cheaper_than_uncached():
    from costlab.estimate import estimate_usd
    m = "anthropic:claude-haiku-4-5-20251001"
    assert estimate_usd(m, 0, 0, cache_read_tokens=7530) < estimate_usd(m, 7530, 0) / 5
