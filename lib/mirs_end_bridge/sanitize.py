"""Input sanitization for player text before it reaches the LLM.

Enforces a length cap, strips control characters and private-use Unicode,
normalizes whitespace, and rejects clearly out-of-character input (URLs,
source code, base64 blobs, repeated-token spam).
"""

from __future__ import annotations

import re
import unicodedata

# ── Length cap ───────────────────────────────────────────────────────────────

MAX_PLAYER_INPUT_LENGTH = 500

TRUNCATION_NARRATOR_LINE = (
    "Argon-87 waits. Long speeches do not move him faster."
)

# ── Rejection patterns ──────────────────────────────────────────────────────

REJECTION_NARRATOR_LINE = "The console rejects your input. Invalid syntax."

# URLs (http/https/ftp)
_URL_RE = re.compile(r"https?://\S+|ftp://\S+", re.IGNORECASE)

# Source-code heuristics: function defs, imports, curly-brace blocks, etc.
_CODE_RE = re.compile(
    r"(?:"
    r"def\s+\w+\s*\(|"
    r"class\s+\w+\s*[:\(]|"
    r"import\s+\w+|"
    r"from\s+\w+\s+import|"
    r"function\s+\w+\s*\(|"
    r"const\s+\w+\s*=|"
    r"let\s+\w+\s*=|"
    r"var\s+\w+\s*=|"
    r"\{\s*\n|"
    r"console\.log|"
    r"print\s*\(|"
    r"System\.out"
    r")",
    re.IGNORECASE,
)

# Base64 blobs (40+ chars of base64 alphabet without spaces)
_BASE64_RE = re.compile(r"[A-Za-z0-9+/=]{40,}")

# Repeated-token spam: same 2-10 char token repeated 8+ times in a row.
# The upper bound on token length avoids catastrophic backtracking on long
# inputs, and the high repeat threshold avoids false positives on natural
# speech patterns like "no no no" or repeated game commands.
_REPEAT_RE = re.compile(r"(.{2,10}?)\1{7,}")

# ── Control-character / private-use stripping ───────────────────────────────

# Control chars (C0/C1) except \n, \r, \t
_CONTROL_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)


def _strip_control_and_private_use(text: str) -> str:
    """Remove control characters and private-use Unicode codepoints."""
    # Strip C0/C1 control chars (except newline, carriage return, tab)
    text = _CONTROL_RE.sub("", text)
    # Strip private-use Unicode ranges
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith("Co"):  # Private Use
            continue
        cleaned.append(ch)
    return "".join(cleaned)


def _normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace to single spaces, strip leading/trailing."""
    return " ".join(text.split())


def _is_suspicious(text: str) -> bool:
    """Return True if the text looks like out-of-character input."""
    if _URL_RE.search(text):
        return True
    if _BASE64_RE.search(text):
        return True
    if _REPEAT_RE.search(text):
        return True
    # Code detection: require at least 2 code-like patterns to avoid
    # false positives on casual use of words like "import" or "class"
    code_matches = _CODE_RE.findall(text)
    if len(code_matches) >= 2:
        return True
    return False


def sanitize_player_input(raw: str) -> tuple[str, str | None]:
    """Sanitize player input text for the LLM prompt.

    Returns a tuple of ``(cleaned_text, narrator_line)``.

    - If *narrator_line* is ``None``, the input is valid and *cleaned_text*
      should be used.
    - If *narrator_line* is a string, the input was rejected or truncated
      and the narrator line should be shown to the player instead of (or
      in addition to) the AI response.

    The cleaned text is always returned (even when truncated) so callers
    can decide whether to still pass it through.
    """
    # Step 1: strip control characters and private-use Unicode
    text = _strip_control_and_private_use(raw)

    # Step 2: normalize whitespace
    text = _normalize_whitespace(text)

    # Step 3: check for suspicious patterns (before truncation)
    if _is_suspicious(text):
        return text, REJECTION_NARRATOR_LINE

    # Step 4: length cap
    narrator: str | None = None
    if len(text) > MAX_PLAYER_INPUT_LENGTH:
        text = text[:MAX_PLAYER_INPUT_LENGTH]
        narrator = TRUNCATION_NARRATOR_LINE

    return text, narrator


def escape_for_xml(text: str) -> str:
    """Escape text for safe inclusion inside XML tags.

    Prevents the player from closing the ``<player_speech>`` block
    by injecting ``</player_speech>`` into their input.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
