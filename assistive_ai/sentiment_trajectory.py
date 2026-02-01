from assistive_ai.bedrock_sentiment import score_sentiment


def build_sentiment_trajectory(structured_call, num_windows=5):
    customer_turns = [
        t for t in structured_call.get("turns", [])
        if t.get("speaker") == "Customer" and t.get("text")
    ]

    if not customer_turns:
        return {
            "sentiment_windows": [],
            "trend": "NEUTRAL"
        }

    call_end = max(t["end"] for t in customer_turns)
    window_size = call_end / num_windows if call_end > 0 else 1

    windows = [[] for _ in range(num_windows)]

    for t in customer_turns:
        idx = int(t["start"] // window_size)
        idx = min(idx, num_windows - 1)
        windows[idx].append(t["text"])

    window_scores = []

    for texts in windows:
        if not texts:
            window_scores.append(0.0)
            continue

        raw_scores = [score_sentiment(t) for t in texts]
        scores = [s for s in raw_scores if s is not None]

        if not scores:
            # All sentiment calls failed → neutral fallback
            window_scores.append(0.0)
            continue

        avg = round(sum(scores) / len(scores), 2)
        window_scores.append(avg)

    trend = determine_trend(window_scores)

    return {
        "sentiment_windows": window_scores,
        "trend": trend
    }


def determine_trend(scores):
    if not scores:
        return "NEUTRAL"

    start = scores[0]
    end = scores[-1]

    if end - start > 0.3:
        return "IMPROVING"
    if start - end > 0.3:
        return "WORSENING"
    return "STABLE"
