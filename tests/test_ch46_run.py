import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ch46_run_sims as c
def near(a, b, t=1e-6): return abs(a - b) < t
def test_ch1(): r = c.ch1(); assert near(r["steps"][-1], 242190) and near(r["factor"], 1.3455)
def test_ch3(): r = c.ch3(); assert near(r["month"], 126000) and r["wk"] > r["month"] > r["we"]
def test_ch10():
    r = c.ch10(); assert r["wed"] < r["thr"] and r["wed"] > r["thr_wed"] and r["sun"] > r["thr_sun"] and r["sun"] < r["thr"]
def test_ch11(): r = c.ch11(); assert near(r["a"], 0.05) and near(r["b"], 0.28) and round(r["accept_needed"], 3) == 0.958
def test_ch14(): r = c.ch14(); assert near(r["ours"], 3.05) and near(r["peer"], 5.72) and near(r["ours_on_peer_mix"], 6.45)
def test_ch17(): r = c.ch17(); assert near(r["noisy"], 0.00785) and round(r["breakeven_cost_of_wrong"], 2) == 0.27
def test_ch18(): r = c.ch18(); assert round(r["need"], 3) == 0.278 and round(r["per_hour"], 2) == 2.94
def test_ch19(): r = c.ch19(); assert near(r["saved"], 115200) and near(r["eng_days"], 76.8)
def test_ch22(): r = c.ch22(); assert near(r["extra"], 500) and near(r["extra_with_cancel"], 200)
def test_ch27(): r = c.ch27(); assert near(r["cost"], 4122.5) and near(r["quality"], 0.938)
def test_ch31(): r = c.ch31(); assert near(r["months"], 12) and round(r["months_after_cut"], 1) == 23.7
def test_ch36(): r = c.ch36(); assert near(sum(r.values()), 90000) and near(r["Search"], 39510)
