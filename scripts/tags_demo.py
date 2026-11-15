#!/usr/bin/env python3
"""Chapter 5: tags from the credential, not from the caller. Synthetic registry."""
from costlab.tags import Credential, resolve_tags
reg = {"k-sa-prod": Credential("k-sa-prod", "support-agent", "support-automation", "production"),
       "k-nq-prod": Credential("k-nq-prod", "nl-query", "insights-platform", "production")}
print(resolve_tags("k-sa-prod", {"feature": "draft-reply", "tenant": "t-0412"}, reg))
print(resolve_tags("k-lambda-old", {"feature": "batch"}, reg))
try:
    resolve_tags("k-sa-prod", {"product": "nl-query"}, reg)
except ValueError as e:
    print("rejected:", e)
