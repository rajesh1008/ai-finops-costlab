import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from exchange_rate_toy import run

def test_flip_with_serving_rule():
    assert run(20, 300, 500, True, False) > run(20, 300, 500, True, True)
    assert run(20, 300, 500, False, False) < run(20, 300, 500, False, True)

def test_keep_with_reuse_cheaper_than_no_reuse():
    assert run(10, 300, 500, True, True) < run(10, 300, 500, False, True)
