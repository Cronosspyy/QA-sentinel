GOOD_CALL_POLICY = {
    "min_qa_score": 85,

    "mandatory_rules": [
        "verification_done",
        "verification_before_issue"
    ],

    "resolution_required": True,

    "allowed_sentiment_trends": [
        "IMPROVING",
        "STABLE"
    ],

    "no_critical_failures": True
}

def is_good_call(qa_result, rule_result, sentiment_result):
    if qa_result["qa_score"] < GOOD_CALL_POLICY["min_qa_score"]:
        return False

    process_rules = rule_result.get("process_rules", {})
    for rule in GOOD_CALL_POLICY["mandatory_rules"]:
        if not process_rules.get(rule, {}).get("passed"):
            return False

    if GOOD_CALL_POLICY["resolution_required"]:
        if qa_result["breakdown"]["resolution"] < 30:
            return False

    if sentiment_result.get("trend") not in GOOD_CALL_POLICY["allowed_sentiment_trends"]:
        return False

    if rule_result.get("compliance", {}).get("critical_fail"):
        return False

    return True
