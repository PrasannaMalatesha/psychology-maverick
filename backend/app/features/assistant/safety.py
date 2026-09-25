"""Crisis detection — the pre-retrieval safety gate (ADR-0004).

Deterministic and conservative: a curated set of acute-risk phrases (suicidal ideation,
self-harm intent), matched case-insensitively. It intentionally over-triggers — ADR-0004's
accepted trade-off is that showing crisis resources when they aren't needed is far cheaper
than missing someone in danger. No model call: this runs before retrieval on every Query and
must be deterministic in tests.

Shortcut: phrase list, not a classifier. It's one function behind a seam; an LLM/classifier
upgrade (M7 evals) swaps `detect_crisis` without touching the graph.
"""

from __future__ import annotations

import re

# Acute-risk phrases, matched on word boundaries, case-insensitive. Scoped to *intent of self-harm*,
# erring toward resources within that scope. Widened in M7 from eval misses: indirect wording,
# common typos ("kil", "my self", "suicidel"), verb forms ("overdosed"), and methods. The eval
# dataset (features/evals) holds the phrasings each pattern exists for — add a case with a pattern.
_CRISIS_PHRASES = [
    r"kill?(?:ing)? my ?self",
    r"(?:hurt|harm|hang)(?:ing)? my ?self",
    r"cut(?:ting)? my ?self",
    r"unaliv(?:e|ing) my ?self",
    r"end(?:ing)? my life",
    r"tak(?:e|ing) my own life",
    r"want to die",
    r"wanna die",
    r"wish i (?:was|were) dead",
    r"better off (?:dead|without me)",
    r"don'?t want to (?:be here|live)",
    r"no reason to live",
    r"nothing to live for",
    r"suicid\w*",
    r"self[\s-]?harm\w*",
    r"overdos\w*",
    r"end(?:ing)? (?:it all|things)",
    r"can'?t (?:go on|take it) anymore",
    r"disappear forever",
    r"asleep and never wake up",
    r"jump(?:ing)? off (?:a|the) (?:bridge|building|roof|cliff)",
]

_CRISIS = re.compile(r"\b(?:" + "|".join(_CRISIS_PHRASES) + r")\b", re.IGNORECASE)


def detect_crisis(text: str) -> bool:
    """True when the text contains an acute-risk signal. Conservative by design (ADR-0004)."""
    return bool(_CRISIS.search(text))
