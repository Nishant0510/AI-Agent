"""
Rule-based prompt injection / jailbreak detection.
 
Deliberately simple regex matching rather than an LLM classifier: it's fast,
runs before any model call, has zero inference cost, and every match is
auditable (you can point at the exact pattern that fired). This is meant as
layer one. An LLM-based classifier can be added later as a second pass for
cases that slip past pattern matching, but should never replace this layer
since it must remain fast/cheap enough to run on every single request.
 
Patterns are grouped by category purely so `reason` strings are informative
in logs. Categories are not otherwise treated differently by the caller.
"""
 
import re
 
# Each pattern is intentionally loose (case-insensitive, partial match) to
# favor catching variants over precision. False positives here just mean an
# occasional legit question gets refused and rephrased; false negatives mean
# an injection reaches the LLM. That asymmetry is why we bias toward recall.
_INJECTION_PATTERNS: dict[str, list[str]] = {
    "instruction_override": [
        r"ignore (all |any )?(the |my )?(previous|prior|above) instructions",
        r"disregard (all |any )?(the |my )?(previous|prior|above) instructions",
        r"forget (all |any )?(the |my )?(previous|prior|above) instructions",
        r"new instructions?:",
        r"override (your |the )?(system|previous) (prompt|instructions?)",
    ],
    "system_prompt_disclosure": [
        r"(reveal|show|print|output|repeat|leak) (your |the )?system prompt",
        r"what (is|are) your (system prompt|instructions)",
        r"repeat (the|your) (words|text) above",
    ],
    "persona_override": [
        r"you are now\b",
        r"act as (if you were |an? )?(?!.{0,40}philips)",
        r"pretend (you are|to be)\b",
        r"from now on,? you (are|will)\b",
        r"enter (developer|debug|admin|god|dan) mode",
        r"jailbreak",
        r"\bdan\b.{0,20}\bmode\b",
    ],
    "knowledge_source_override": [
        r"answer (this |that )?from your (general|internal|own|training) knowledge",
        r"ignore the (documents?|manuals?|context|retrieved) and answer",
        r"don'?t use the (documents?|manuals?|retrieved context)",
        r"make (something|it) up",
        r"just (guess|invent|fabricate) (an? )?answer",
    ],
    "destructive_operation": [
        r"delete (the |all )?(vector|faiss|index|database|documents?)",
        r"drop (the )?(table|index|database|collection)",
        r"clear (the )?(vector store|database|index|memory)",
        r"reset (the )?(vector store|database|index)",
    ],
}
 
_COMPILED: list[tuple[str, re.Pattern]] = [
    (category, re.compile(pattern, re.IGNORECASE))
    for category, patterns in _INJECTION_PATTERNS.items()
    for pattern in patterns
]
 
 
def detect_unsafe_input(question: str) -> tuple[bool, str | None]:
    """
    Scan a user question for prompt injection / jailbreak patterns.
 
    Returns:
        (is_unsafe, reason) — reason is an internal-only diagnostic string
        (category + matched pattern), never meant to be shown to the user.
        Returns (False, None) when nothing matches.
    """
    if not question or not question.strip():
        return False, None
 
    for category, pattern in _COMPILED:
        if pattern.search(question):
            return True, f"{category}: matched pattern '{pattern.pattern}'"
 
    return False, None