PII_KEYWORDS = ["account number", "card number", "cvv"]
MANDATORY_SCRIPT = ["recorded for quality"]

def run_compliance_rules(structured_call):
    turns = structured_call["turns"]

    # Rule 1: Mandatory disclosure
    # if not any(
    #     t["speaker"] == "Agent" and any(s in t["text"].lower() for s in MANDATORY_SCRIPT)
    #     for t in turns
    # ):
    #     return critical_fail("Mandatory disclosure missing")

    # Rule 2: PII before verification
    verified = False
    for t in turns:
        if "verify" in t["text"].lower():
            verified = True
        if not verified and any(p in t["text"].lower() for p in PII_KEYWORDS):
            return critical_fail("PII shared before verification")

    return {"critical_fail": False}


def critical_fail(reason):
    return {
        "critical_fail": True,
        "reason": reason
    }
