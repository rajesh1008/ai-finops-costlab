"""38th run: arithmetic behind the new illustrative sections. All inputs are invented and labelled so in the text, except tokens 635.8 and 851.4 which come from runs/gold-position-lab-2026-11-13.jsonl."""
def tokenizer_undercount(old=635.8, new=851.4):
    return {"undercount": 1 - old / new, "newer_extra": new / old - 1}
def cascade_blend(student=0.0008, large=0.006, fallback=0.2, calls=400_000):
    per = student + fallback * large
    return {"per_call": per, "saving_vs_large": 1 - per / large, "monthly": per * calls,
            "breakeven_fallback": (large - student) / large}
def batch_late(discount=0.5, miss=0.1):
    return {"cost_per_job": (1 - discount) + miss, "saving": 1 - ((1 - discount) + miss), "breakeven_miss": discount}
def waste_per_success(spend=52_000, sessions=40_000, bad=6_400, bad_cost=11_700, cut=1 / 3):
    good = sessions - bad
    return {"per_success": spend / good, "clean": (spend - bad_cost) / good,
            "overhead": spend / good / ((spend - bad_cost) / good) - 1,
            "after_cut": (spend - cut * bad_cost) / good}
def price_floor(cost=0.40, success=0.62, margin=0.70):
    return cost / success / (1 - margin)
def checkpoint(err=0.03, review=1.20, catch=0.8, err_cost=40):
    return {"none": err * err_cost, "with": review + err * (1 - catch) * err_cost, "breakeven_cost": review / (err * catch)}
if __name__ == "__main__":
    for f in (tokenizer_undercount, cascade_blend, batch_late, waste_per_success, price_floor, checkpoint): print(f.__name__, f())
    print(cascade_blend(fallback=0.35), price_floor(success=0.55), checkpoint(err_cost=200), batch_late(miss=0.2))
