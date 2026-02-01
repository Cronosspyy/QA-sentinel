def generate_city_coaching(city, analyzed_calls):
    issue_agents = defaultdict(set)

    for call in analyzed_calls:
        agent = call["agent_id"]
        for reason in call["qa_result"]["explanations"]:
            issue_agents[reason].add(agent)

    top_issue = max(issue_agents.items(), key=lambda x: len(x[1]))

    return {
        "city": city,
        "call_volume": len(analyzed_calls),
        "top_issue": {
            "issue": top_issue[0],
            "agents_affected": len(top_issue[1])
        },
        "root_cause_hypothesis": "Likely process or training gap"
    }
