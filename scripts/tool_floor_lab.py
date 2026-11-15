"""Ch2: the tool-use floor. count_tokens with and without one small tool, per model."""
import json, os, sys, datetime
import anthropic
c = anthropic.Anthropic()
TOOL = {"name": "get_previous_tickets", "description": "Return a customer's previous support tickets.",
        "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}}
SYS = "You are a support assistant for a B2B analytics product. Answer briefly."
Q = [{"role": "user", "content": "How do I reset my dashboard password?"}]
out = []
for m in ("claude-haiku-4-5", "claude-haiku-5-5"):
    row = {"model": m}
    try:
        base = c.messages.count_tokens(model=m, system=SYS, messages=Q).input_tokens
        auto = c.messages.count_tokens(model=m, system=SYS, messages=Q, tools=[TOOL]).input_tokens
        forced = c.messages.count_tokens(model=m, system=SYS, messages=Q, tools=[TOOL], tool_choice={"type": "tool", "name": "get_previous_tickets"}).input_tokens
        row.update(no_tools=base, one_tool_auto=auto, one_tool_forced=forced, auto_minus_base=auto - base, forced_minus_base=forced - base)
    except Exception as e:
        row["error"] = type(e).__name__ + ": " + str(e)[:120]
    out.append(row)
    print(row)
p = f"runs/tool-floor-{datetime.date.today()}.json"
json.dump(out, open(p, "w"), indent=1)
