def generate_supervisor_alert(call):
    qa = call["qa_result"]
    sentiment = call["sentiment_result"]
    compliance = call["rule_result"].get("compliance", {})

    reasons = []

    # CRITICAL
    if compliance.get("critical_fail"):
        reasons.append("Critical compliance failure")
        return {
            "level": "CRITICAL",
            "action": "Immediate review required",
            "reasons": reasons
        }

    if qa["qa_score"] < 40:
        reasons.append("Very low QA score")
        return {
            "level": "CRITICAL",
            "action": "Immediate review required",
            "reasons": reasons
        }

    if sentiment["trend"] == "WORSENING" and qa["breakdown"]["resolution"] == 0:
        reasons.append("Customer sentiment worsened without resolution")
        return {
            "level": "CRITICAL",
            "action": "Immediate review required",
            "reasons": reasons
        }

    # HIGH
    if qa["qa_score"] < 55:
        reasons.append("Low QA score")
        return {
            "level": "HIGH",
            "action": "Review within 24 hours",
            "reasons": reasons
        }

    return None
