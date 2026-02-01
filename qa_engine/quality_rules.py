def run_quality_rules(structured_call):
    turns = structured_call["turns"]

    return {
        "interruptions": count_interruptions(turns),
        "long_silences": detect_silence(turns),
        "agent_talk_ratio": agent_talk_ratio(turns)
    }


def count_interruptions(turns):
    return sum(1 for t in turns if t.get("interrupted", False))


def detect_silence(turns):
    long_silences = []
    for t in turns:
        if t.get("silence_after", 0) > 20:
            long_silences.append({
                "turn_id": t["turn_id"],
                "silence": t["silence_after"]
            })
    return long_silences


def agent_talk_ratio(turns):
    agent_words = 0
    total_words = 0

    for t in turns:
        words = len(t["text"].split())
        total_words += words
        if t["speaker"] == "Agent":
            agent_words += words

    return round(agent_words / total_words, 2) if total_words else 0
