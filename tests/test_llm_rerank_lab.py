import importlib.util, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "llm_rerank_lab.py"
s = importlib.util.spec_from_file_location("lrl", p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
def test_questions_and_order():
    assert len(m.QS) == 20
    for i, (plan, kind, q, ans, pos) in enumerate(m.QS):
        od = m.order(plan, pos, i)
        assert len(od) == 12 and len(set(od)) == 12 and od[pos - 1] == plan
