# Informational-only safety posture with crisis-first routing

The assistant is an **informational/educational** tool: it explains what authoritative sources say
about psychology, psychiatry, and mental health, always grounded and cited. It **does not**
diagnose, prescribe, or give personalized treatment advice. A crisis-detection step runs **before**
retrieval and, on acute-risk signals, surfaces crisis resources and stops — safety takes priority
over answering.

## Why

- The corpus is mental-health-adjacent and some users will arrive distressed. An LLM giving
  personalized mental-health *advice* to vulnerable people is a genuine harm and liability; we are
  not a licensed provider.
- "Safe by construction" (routing, refusal, disclaimers, human-in-the-loop) is far stronger than a
  footnote disclaimer, and it demonstrates judgment, not just capability.

## How it shows up in the system

- **Crisis node first** in the LangGraph flow; can short-circuit the whole graph. Detection errs
  toward showing resources (default US 988 + international `findahelpline.com`, region-configurable).
- **Faithfulness judge** blocks ungrounded claims at runtime; `insufficient_context` is a
  first-class answer state.
- **Human-in-the-loop interrupt** for low-confidence clinical answers.
- **Clinical disclaimer** on clinical-category answers.

## Consequences

- The assistant will sometimes decline to "help" in the way a user asks (e.g. refuse to diagnose),
  by design. A future maintainer must not "fix" this by loosening the posture.
- Crisis detection is intentionally conservative and may over-trigger; that is the accepted
  trade-off.
