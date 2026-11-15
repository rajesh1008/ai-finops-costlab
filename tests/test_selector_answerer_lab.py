import importlib.util, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "selector_answerer_lab.py"
s = importlib.util.spec_from_file_location("sal", p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
def test_order_puts_gold_at_position():
    for i, (pl, kind, q, ans, pos) in enumerate(m.QS):
        od = m.order(pl, pos, i); assert len(od) == 40 and len(set(od)) == 40 and od[pos - 1] == pl
def test_answers_are_in_passages():
    for pl, kind, q, ans, pos in m.QS: assert ans in m.passage(pl)
def test_cost_helper():
    rows = [{"direct": {"in": 1000, "out": 10}}]
    assert abs(m.cost(rows, [("direct", m.ANS)]) - (1000 * 1.0 + 10 * 5.0) / 1e6 * 1000) < 1e-9
