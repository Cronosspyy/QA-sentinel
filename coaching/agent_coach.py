from collections import Counter, defaultdict

def generate_agent_coaching(agent_id, analyzed_calls):
    rule_failures = Counter()
    qa_scores = []
    examples = defaultdict(list)

    for call in analyzed_calls:
        qa_scores.append(call["qa_result"]["qa_score"])

        for reason in call["qa_result"]["explanations"]:
            rule_failures[reason] += 1
            if len(examples[reason]) < 2:
                examples[reason].append(call["call_id"])

    if not rule_failures:
        return {
            "agent_id": agent_id,
            "status": "NO_COACHING_REQUIRED"
        }

    top_issue, count = rule_failures.most_common(1)[0]

    return {
        "agent_id": agent_id,
        "call_volume": len(analyzed_calls),
        "qa_average": round(sum(qa_scores) / len(qa_scores), 1),
        "primary_coaching_theme": top_issue,
        "themes": [
            {
                "issue": top_issue,
                "frequency": f"{count} / {len(analyzed_calls)} calls",
                "example_calls": examples[top_issue]
            }
        ],
        "recommended_focus": top_issue
    }
