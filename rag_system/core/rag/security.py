import re

BLOCK_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all rules",
    r"reveal system prompt",
    r"show hidden prompt",
    r"developer message",
    r"print api key",
    r"disable safety",
]

def detect_prompt_injection(text):
    text = text.lower().strip()

    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, text):
            return True

    return False