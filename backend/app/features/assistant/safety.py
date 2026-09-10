"""Crisis detection — the pre-retrieval safety gate (ADR-0004).

Deterministic and conservative: a curated set of acute-risk phrases (suicidal ideation,
self-harm intent), matched case-insensitively. It intentionally over-triggers — ADR-0004's
accepted trade-off is that showing crisis resources when they aren't needed is far cheaper
than missing someone in danger. No model call: this runs before retrieval on every Query and
must be deterministic in tests.

ponytail: phrase list, not a classifier. It's one function behind a seam; an LLM/classifier
upgrade (M7 evals) swaps `detect_crisis` without touching the graph.
"""

from __future__ import annotations

import re

# Acute-risk phrases. Flexible inner whitespace; matched on word boundaries, case-insensitive.
# Kept deliberately narrow to *intent of self-harm* — not every mention of the topic, but erring
# toward resources within that scope.
_CRISIS_PHRASES = [
    r"kill(?:ing)? myself",
    r"end(?:ing)? my life",
    r"take my own life",
    r"taking my own life",
    r"want to die",
    r"wanna die",
    r"wish i (?:was|were) dead",
    r"better off dead",
    r"don'?t want to (?:be here|live)",
    r"no reason to live",
    r"nothing to live for",
    r"suicidal",
    r"suicide",
    r"self[\s-]?harm",
    r"hurt myself",
    r"hurting myself",
    r"harm myself",
    r"harming myself",
    r"cut myself",
    r"cutting myself",
    r"overdose",
]

_CRISIS = re.compile(r"\b(?:" + "|".join(_CRISIS_PHRASES) + r")\b", re.IGNORECASE)


def detect_crisis(text: str) -> bool:
    """True when the text contains an acute-risk signal. Conservative by design (ADR-0004)."""
    return bool(_CRISIS.search(text))
