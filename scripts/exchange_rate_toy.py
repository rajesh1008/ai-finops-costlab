"""Toy model inspired by the Think-or-Remember framing (arXiv 2611.10982).
NOT the paper's model. Every number is an ASSUMPTION of this book.
Cost of one call = c * (tokens processed) + beta * (pairs attended).
A call that reuses the stored state processes only the new tokens; one that does not
reprocesses the whole transcript. Attention pairs: each processed token attends to
all tokens before it. We compare keeping and dropping earlier reasoning."""
import sys

def run(steps, obs, reason, reuse, keep, c=1.0, beta=0.0005):
    # Stored state survives only if the prefix is unchanged: dropping earlier reasoning edits
    # the prefix, so the server must reprocess the history even if it can reuse state.
    reuse = reuse and keep
    hist = 0          # tokens of history in the prompt
    total = 0.0
    for _ in range(steps):
        new = obs + (0 if reuse else 0)
        if reuse:
            proc = new + reason            # new tokens plus this step's reasoning (generated)
            pairs = proc * hist + proc * proc / 2
        else:
            proc = hist + new              # reprocess prompt
            pairs = proc * proc / 2 + reason * (proc + reason / 2)
            proc += reason
        total += c * proc + beta * pairs
        hist += obs + (reason if keep else 0)
    return total

if __name__ == "__main__":
    obs, reason = 300, 500
    print("assumed: observation 300 tokens/step, reasoning 500 tokens/step, c=1, beta=0.0005")
    print("P* = c/beta = 2000 tokens (the toy's exchange rate)")
    print(f"{'steps':>5} {'reuse':>6} {'keep':>10} {'drop':>10} {'drop/keep':>10}")
    for reuse in (True, False):
        for steps in (5, 10, 20, 40):
            k = run(steps, obs, reason, reuse, True)
            d = run(steps, obs, reason, reuse, False)
            print(f"{steps:>5} {str(reuse):>6} {k:>10.0f} {d:>10.0f} {d/k:>10.2f}")
