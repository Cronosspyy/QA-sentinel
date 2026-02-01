SOP_MAP = {
    "battery": ["reset", "retry", "escalate"]
}

def run_sop_rules(structured_call):
    turns = structured_call["turns"]
    detected_steps = set()

    for t in turns:
        text = t["text"].lower()
        for step in SOP_MAP.get("battery", []):
            if step in text:
                detected_steps.add(step)

    return {
        "required_steps": SOP_MAP["battery"],
        "completed_steps": list(detected_steps),
        "missing_steps": list(set(SOP_MAP["battery"]) - detected_steps)
    }
