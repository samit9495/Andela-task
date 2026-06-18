"""Sanitize untrusted text before it enters an LLM prompt (prompt-injection defense)."""

import re

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_INJECTION_MARKERS = re.compile(
    r"<\|im_(?:start|end)\|>|###\s*system|###\s*instructions|<<<\s*end\s*>>>",
    flags=re.IGNORECASE,
)
MAX_FIELD_LEN = 1000


def sanitize(text: str) -> str:
    """Strip control chars and injection markers, then truncate."""
    text = _CONTROL.sub("", text)
    text = _INJECTION_MARKERS.sub("[REDACTED]", text)
    return text[:MAX_FIELD_LEN]
