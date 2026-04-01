def classify_query(query: str):
    query = query.lower()

    # factual
    if any(word in query for word in ["what", "define", "who", "when"]):
        return "factual"

    # conceptual
    elif any(word in query for word in ["explain", "how", "working", "process"]):
        return "conceptual"

    # analytical
    elif any(word in query for word in ["why", "impact", "benefit", "importance"]):
        return "analytical"

    # default
    return "keyword"