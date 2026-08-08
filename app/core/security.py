"""Security utilities for the AI Interview Agent."""

import re
from typing import Optional


# Known prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"system\s*:\s*",
    r"###\s*instruction",
    r"reveal\s+(your|the)\s+(system|hidden|internal)",
    r"show\s+me\s+(your|the)\s+prompt",
    r"what\s+are\s+your\s+instructions",
    r"disregard\s+(all|previous)",
    r"override\s+your",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> bool:
    """Detect potential prompt injection attempts in candidate input."""
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitize user input."""
    if not text:
        return ""
    # Truncate to max length
    text = text[:max_length]
    # Remove null bytes
    text = text.replace("\x00", "")
    return text.strip()


def validate_interview_id(interview_id: str) -> bool:
    """Validate interview ID format."""
    if not interview_id:
        return False
    # Allow alphanumeric, hyphens, underscores
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,64}$", interview_id))


def validate_candidate_id(candidate_id: str) -> bool:
    """Validate candidate ID format."""
    if not candidate_id:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,64}$", candidate_id))
