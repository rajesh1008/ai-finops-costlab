"""Chapter 17 follow-up (nineteenth run): a HARDER synthetic billing problem (discount, prorated refund for unused months, tax), exact answers, and a safe evaluator for the 'write an expression, let the harness compute' arm.
All problems are SYNTHETIC and author-generated. Reuses correct/agree/final_number from costlab.cascade."""
import random, ast, operator
from costlab.cascade import correct, agree, final_number  # noqa: F401
def make_hard(n=40, seed=19):
    rnd = random.Random(seed); out = []
    for i in range(n):
        s = rnd.randint(12, 40); p = rnd.choice([29, 39, 45, 49, 59, 79]); d = rnd.choice([5, 10, 12, 15, 20, 25]); r = rnd.randint(2, max(2, s // 3))
        m = rnd.randint(2, 9); t = rnd.choice([5, 8, 10, 18, 20])
        ans = round((s * p * (1 - d / 100) - r * p * (1 - d / 100) * (12 - m) / 12) * (1 + t / 100), 2)
        q = (f"A customer bought an annual plan for {s} seats at ${p} per seat per year. A {d} percent discount applies to the whole purchase. After {m} months the customer cancelled {r} seats "
             f"and is refunded for the unused months of those seats, prorated monthly, at the discounted per-seat price. Then {t} percent tax is applied to the net amount after the refund. What is the final amount charged?")
        out.append({"id": i, "q": q, "answer": ans})
    return out
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg}
def safe_eval(expr):
    """Evaluate a pure arithmetic expression (numbers, + - * / and parentheses). Anything else raises ValueError."""
    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool): return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS: return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported")
    return ev(ast.parse(expr.strip().strip("`").strip(), mode="eval"))
