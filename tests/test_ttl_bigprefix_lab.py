import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ttl_bigprefix_lab as T
def rows():
    return [json.loads(l) for l in T.OUT.read_text().splitlines()]
def test_committed_run_shape():
    r = rows()
    assert len(r) == 6 and all("error" not in u for x in r for u in x["rows"])
def test_one_hour_write_costs_more_and_reads_match():
    s = T.summarise(rows())
    assert s["1h"]["write_call_cost"] > 1.5 * s["5m"]["write_call_cost"]
    assert s["1h"]["reads"] == s["5m"]["reads"] == 9
def test_write_lands_in_the_field_for_its_lifetime():
    for x in rows():
        w = x["rows"][0]
        if x["ttl"] == "1h": assert w["cw1h_field"] == w["cw"] and w["cw5m_field"] == 0
        else: assert w["cw5m_field"] == w["cw"] and w["cw1h_field"] == 0
