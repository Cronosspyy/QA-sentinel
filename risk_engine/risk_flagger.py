def compute_risk(call_id, rule_result, sentiment_result):
    reasons = []
    risk_score = 0

    # 1. Compliance is absolute
    compliance = rule_result.get("compliance", {})
    if compliance.get("critical_fail"):
        return {
            "call_id": call_id,
            "risk_level": "HIGH",
            "priority_score": 3,
            "reasons": [compliance.get("reason", "Compliance violation")]
        }

    # 2. Process rule failures
    process_rules = rule_result.get("process_rules", {})
    failed_process = [
        name for name, res in process_rules.items()
        if not res.get("passed", True)
    ]

    if len(failed_process) >= 2:
        risk_score += 1
        reasons.append("Multiple process violations")

    # 3. Sentiment trajectory
    if sentiment_result.get("trend") == "WORSENING":
        risk_score += 1
        reasons.append("Customer sentiment worsened")

    # 4. Long silences
    long_silences = rule_result.get("quality_signals", {}).get("long_silences", [])
    if long_silences:
        risk_score += 1
        reasons.append("Extended silence detected")

    # 5. Determine final risk level
    if risk_score >= 2:
        level = "HIGH"
    elif risk_score == 1:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "call_id": call_id,
        "risk_level": level,
        "priority_score": risk_score,
        "reasons": reasons
    }
