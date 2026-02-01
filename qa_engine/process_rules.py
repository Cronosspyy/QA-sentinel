GREETING_KEYWORDS = ["hello", "hi", "good morning", "good evening"]
VERIFICATION_KEYWORDS = ["verify", "confirm", "date of birth", "registered"]
CLOSING_KEYWORDS = ["anything else", "further assistance"]

def run_process_rules(structured_call):
    turns = structured_call["turns"]
    results = {}

    results["greeting_present"] = check_greeting(turns)
    results["verification_done"] = check_verification(turns)
    results["verification_before_issue"] = check_verification_order(turns)
    results["closing_offer_present"] = check_closing(turns)

    return results


def check_greeting(turns):
    for t in turns:
        if t["phase"] == "OPENING" and t["speaker"] == "Agent":
            if any(k in t["text"].lower() for k in GREETING_KEYWORDS):
                return pass_rule("Greeting detected", t)
    return fail_rule("No greeting in opening phase")


def check_verification(turns):
    for t in turns:
        if t["speaker"] == "Agent":
            if any(k in t["text"].lower() for k in VERIFICATION_KEYWORDS):
                return pass_rule("Verification attempted", t)
    return fail_rule("No verification attempted")


def check_verification_order(turns):
    verification_turn = None
    issue_turn = None

    for t in turns:
        if verification_turn is None and any(
            k in t["text"].lower() for k in VERIFICATION_KEYWORDS
        ):
            verification_turn = t["turn_id"]

        if issue_turn is None and t["phase"] == "ISSUE_IDENTIFICATION":
            issue_turn = t["turn_id"]

    if verification_turn and issue_turn and verification_turn < issue_turn:
        return {
            "passed": True,
            "evidence": "Verification occurred before issue discussion",
            "turn_ids": [verification_turn, issue_turn]
        }

    return {
        "passed": False,
        "evidence": "Issue discussed before verification",
        "turn_ids": []
    }


def check_closing(turns):
    for t in turns[::-1]:
        if t["phase"] == "CLOSING" and t["speaker"] == "Agent":
            if any(k in t["text"].lower() for k in CLOSING_KEYWORDS):
                return pass_rule("Closing offer present", t)
    return fail_rule("No closing offer found")


def pass_rule(msg, turn):
    return {
        "passed": True,
        "evidence": msg,
        "turn_ids": [turn["turn_id"]]
    }


def fail_rule(msg):
    return {
        "passed": False,
        "evidence": msg,
        "turn_ids": []
    }
