#!/usr/bin/env python3
"""Chapter 4 failure injection: an outcome the model can emit without the user benefiting.

SYNTHETIC. 10,000 support conversations in a month, generated with a fixed seed from stated
assumptions (printed below). Nothing here is a measurement of a real product.
"""
import random
from costlab.outcome import Window, three_denominators, OutcomeContract

random.seed(4)
N = 10_000
cost = 25_350.0   # the support-agent's tagged October invoice lines, from the Fieldstone fixture
P_ACCEPT = 0.82          # assumed: share of drafts that pass a rubric check
P_RECONTACT_GIVEN_ACCEPT = 0.19   # assumed: accepted drafts followed by the same customer writing again within 7 days
P_RECONTACT_GIVEN_REJECT = 0.55
accepted = benefited = 0
for _ in range(N):
    acc = random.random() < P_ACCEPT
    if acc:
        accepted += 1
        if random.random() > P_RECONTACT_GIVEN_ACCEPT:
            benefited += 1
w = Window(cost_usd=cost, emitted=N, accepted=accepted, benefited=benefited)
r = three_denominators(w)
print(f"assumptions: n={N}, accept={P_ACCEPT}, recontact|accept={P_RECONTACT_GIVEN_ACCEPT}, seed=4")
print(f"emitted {w.emitted}  accepted {w.accepted}  benefited {w.benefited}")
print(f"cost per emitted response   ${r['per_emitted']:.4f}")
print(f"cost per accepted response  ${r['per_accepted']:.4f}")
print(f"cost per benefited response ${r['per_benefited']:.4f}")
print(f"the first number understates the third by {1 - r['per_emitted']/r['per_benefited']:.1%}")

print()
c = OutcomeContract(product="support-agent", outcome_statement="A customer's issue is resolved and does not return within seven days.",
                    counted_event="ticket state 'resolved' with no new ticket from the same customer on the same topic in 7 days",
                    quality_bar="rubric score at or above the agreed floor on the sampled review set")
print("contract check, unsigned draft:", "missing " + ", ".join(c.missing()))
