import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ch38_run_sims as s
def test_tokenizer(): assert round(s.tokenizer_undercount()["undercount"], 3) == 0.253
def test_cascade():
    c = s.cascade_blend(); assert round(c["per_call"], 6) == 0.002 and round(c["breakeven_fallback"], 3) == 0.867
    assert round(s.cascade_blend(fallback=0.35)["monthly"]) == round(0.0029 * 400000)
def test_batch(): assert round(s.batch_late(miss=0.1)["saving"], 2) == 0.40
def test_waste():
    w = s.waste_per_success(); assert round(w["per_success"], 3) == 1.548 and round(w["clean"], 3) == 1.199
def test_price(): assert round(s.price_floor(), 2) == 2.15 and round(s.price_floor(success=.55), 2) == 2.42
def test_checkpoint():
    assert round(s.checkpoint()["with"], 2) == 1.44 and round(s.checkpoint()["breakeven_cost"]) == 50
