"""Chapter 16: synthetic support tickets with known labels, and a keyword rule set. SYNTHETIC."""
import random, re

LABELS = ["billing", "password", "shipping", "cancel", "other"]

CLEAR = {
 "billing": ["I was charged twice on my last invoice", "Why is there an extra fee on my invoice this month",
             "Please send me a copy of invoice 4471", "My invoice shows the wrong amount"],
 "password": ["I forgot my password and the reset email never arrives", "How do I reset my password",
              "Password reset link has expired", "I cannot log in, I need a password reset"],
 "shipping": ["Where is my order, the shipping page says in transit for nine days", "Tracking number shows no update",
              "My package has not arrived and the shipping estimate has passed", "Can you check the shipping status of my order"],
 "cancel": ["I want to cancel my subscription", "Please cancel my plan before it renews",
            "How do I cancel my account", "Cancel my subscription effective today"],
 "other": ["Do you have a dark mode", "Can I export my data to a spreadsheet", "Is there a mobile app",
           "What languages do you support"],
}
# Hard cases: no keyword, or a misleading keyword. Label is what a careful human would pick.
HARD = [
 ("The thing you sent me last week is still sitting at the depot", "shipping"),
 ("I keep getting locked out and typing my old credentials does nothing", "password"),
 ("I would rather not pay you any more after this month", "cancel"),
 ("The number at the bottom of the email you sent looks higher than what we agreed", "billing"),
 ("I cancelled my order but you still charged me on the invoice", "billing"),
 ("Can you reset the dashboard filters, I changed them by mistake", "other"),
 ("Please stop the renewal, I am moving to another tool", "cancel"),
 ("My parcel was delivered to a neighbour, who do I contact about the refund of shipping", "shipping"),
]

RULES = [
 ("password", r"password|log in|login"),
 ("cancel", r"\bcancel(?!led)"),
 ("shipping", r"shipping|tracking|package|order\b"),
 ("billing", r"invoice|charged|fee\b"),
]

def rule_label(text):
    t = text.lower()
    for label, pat in RULES:
        if re.search(pat, t):
            return label
    return None   # no rule fired

def make_tickets(n=100, hard_share=0.3, seed=16):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        if rnd.random() < hard_share:
            t, y = rnd.choice(HARD)
        else:
            y = rnd.choice(LABELS)
            t = rnd.choice(CLEAR[y])
        out.append({"id": i, "text": t, "label": y})
    return out
