def handbook() -> str:
    clauses = []
    for i in range(1, 161):
        clauses.append(f"Clause {i}. For workspace tier {i % 7 + 1}, a support agent must verify the account "
                       f"owner, record reference FS-{1000 + i * 13}, and confirm the retention window of "
                       f"{30 + (i % 12) * 15} days before describing any export or deletion procedure.")
    return "Fieldstone Analytics support handbook (synthetic).\n" + "\n".join(clauses)
