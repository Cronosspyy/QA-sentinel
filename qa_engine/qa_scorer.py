# qa_engine/qa_scorer.py

def score_call(rule_result, sentiment_result):
    explanations = []

    # --------------------
    # 1. PROCESS ADHERENCE (35)
    # --------------------
    process_score = 0
    process_rules = rule_result.get("process_rules", {})

    if process_rules.get("greeting_present", {}).get("passed"):
        process_score += 5
    else:
        explanations.append("Greeting was missing")

    if process_rules.get("verification_done", {}).get("passed"):
        process_score += 10
    else:
        explanations.append("Verification was skipped")

    if process_rules.get("verification_before_issue", {}).get("passed"):
        process_score += 5
    else:
        explanations.append("Issue discussed before verification")

    if process_rules.get("closing_offer_present", {}).get("passed"):
        process_score += 5
    else:
        explanations.append("Call was not properly closed")

    sop = rule_result.get("sop_alignment", {})
    required = sop.get("required_steps", [])
    completed = sop.get("completed_steps", [])

    if required:
        completion_ratio = len(completed) / len(required)
        sop_score = round(completion_ratio * 10)
        process_score += sop_score

        if completion_ratio < 1:
            missing = sop.get("missing_steps", [])
            explanations.append(
                f"SOP steps missing: {', '.join(missing)}"
            )
    else:
        process_score += 10

    process_score = min(process_score, 35)

    # --------------------
    # 2. RESOLUTION CORRECTNESS (30)
    # --------------------
    resolution_score = 0

    if required:
        if len(completed) == len(required):
            resolution_score = 30
        elif completed:
            resolution_score = round(30 * (len(completed) / len(required)))
            explanations.append("Resolution was partially completed")
        else:
            resolution_score = 0
            explanations.append("No resolution steps were attempted")
    else:
        resolution_score = 30

    # --------------------
    # 3. SENTIMENT (25)
    # --------------------
    sentiment_score = 0
    trend = sentiment_result.get("trend", "NEUTRAL")

    if trend == "IMPROVING":
        sentiment_score = 25
        explanations.append("Customer sentiment improved during the call")
    elif trend == "STABLE":
        sentiment_score = 15
        explanations.append("Customer sentiment remained stable")
    elif trend == "WORSENING":
        sentiment_score = 5
        explanations.append("Customer sentiment worsened during the call")

    # --------------------
    # 4. COMPLIANCE (10)
    # --------------------
    compliance = rule_result.get("compliance", {})
    critical_fail = compliance.get("critical_fail", False)

    if critical_fail:
        compliance_score = 0
        explanations.append("Critical compliance failure detected")
    else:
        compliance_score = 10

    # --------------------
    # FINAL SCORE
    # --------------------
    total_score = (
        process_score
        + resolution_score
        + sentiment_score
        + compliance_score
    )

    # Compliance override
    if critical_fail:
        total_score = min(total_score, 49)

    # --------------------
    # BAND
    # --------------------
    if total_score >= 85:
        band = "GOOD"
    elif total_score >= 70:
        band = "COACHING"
    elif total_score >= 50:
        band = "POOR"
    else:
        band = "HIGH_RISK"

    return {
        "qa_score": total_score,
        "band": band,
        "breakdown": {
            "process": process_score,
            "resolution": resolution_score,
            "sentiment": sentiment_score,
            "compliance": compliance_score
        },
        "explanations": explanations
    }
