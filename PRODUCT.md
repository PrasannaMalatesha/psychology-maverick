# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (App Router) + TypeScript, Tailwind CSS, shadcn/ui, and the Vercel AI SDK for streaming.
Decided during the project's design interview (see [project.md](project.md) §11 and
[docs/PRD.md](docs/PRD.md) §6.8); recorded here as confirmed, not delegated.

## Users

Two primary audiences, one informational posture:

- **The Learner** — a student or curious person exploring psychology or psychiatry, wanting
  accurate, cited explanations at academic depth ("what does research say about X?").
- **The Clarity-Seeker** — someone trying to understand a mental-health topic for themselves or a
  loved one, wanting plain-language, reassuring, authoritative information ("what are the signs of
  depression?").

Secondary: **Admin** (corpus maintainer — ingest/refresh, corpus stats). Meta-audience: a
**Reviewer/interviewer** evaluating this as a portfolio artifact.

## Product Purpose

A retrieval-grounded assistant that answers questions about psychology, psychiatry, and mental
health strictly from a curated, openly-licensed corpus, citing every claim back to its source.
Success = grounded, verifiable, appropriately-toned answers; zero unsafe handling of users in
distress; and a system a reviewer can run and trust.

## Positioning

Unlike a general chatbot, every answer is **grounded in a known corpus and cited to the passage**
that supports it — and the product is **safe by construction** for a vulnerable audience
(crisis-first routing, informational-only, never diagnosis or personalized advice). It refuses to
answer beyond its corpus rather than hallucinating.

## Operating Context

- Used in a browser, often reflectively; some users arrive distressed.
- Two intents share one surface: *learning* (academic depth) and *clarity* (plain language). The
  UI must serve both without making a distressed user feel they're reading a textbook.
- Answers stream in; conversations are multi-turn and persist per user.
- Citations are central to trust: a user should be able to see exactly which source (OpenStax
  chapter, PLOS article, NIMH brochure) grounds each claim.

## Capabilities and Constraints

- Grounded RAG over three registers (textbook, research, consumer health) spanning psychology and
  psychiatry; structured, cited answers; multi-turn chat; crisis escalation; faithfulness checks.
- Terminology is canonical — see [CONTEXT.md](CONTEXT.md) (Query, Answer, Citation, Category,
  Insufficient Context, Crisis Escalation, Faithfulness).
- Constraint: answers come only from the corpus; out-of-corpus questions return
  `insufficient_context`.

## Brand Commitments

- **Product name: Psychology Maverick.** (The earlier "Casebook" wordmark was a working placeholder.)
- **Voice:** calm, credible, plain-spoken; never clinical-cold, never hype, never gamified.
- **Visual system: MindMarket** (installed at `design-system/`, documented in [DESIGN.md](DESIGN.md)).
  A warm storybook system on cream paper: giant Inter display, grass-green as a structural accent
  only, 50px pill radii, surface-stack elevation (no shadows), coral for the service action, a
  yellow closing band. This supersedes the earlier "Case Notes" world. **Constraint for this
  product:** crisis and clinical states must stay visually credible within the playful system, so a
  distressed user is never met with something toy-like.
- No AI/tooling attribution anywhere in the product.

## Evidence on Hand

- Real, openly-licensed corpus already ingested: OpenStax *Psychology 2e*, 25 PLOS ONE articles
  (psychology + psychiatry), 4 NIMH brochures — see [data/corpus/SOURCES.md](data/corpus/SOURCES.md).
- No real users, testimonials, benchmarks, or production metrics yet — future work must not
  fabricate these. Demonstration Q&A shown in UI must be labeled synthetic where a viewer could
  mistake it for real product output.

## Product Principles

1. **Grounded or silent** — cite the corpus or say `insufficient_context`; never invent.
2. **Safety over helpfulness** — a user in crisis gets resources, not a corpus answer.
3. **Informational, never advisory** — explain what sources say; never diagnose or prescribe.
4. **Two intents, one calm surface** — serve learner depth and clarity-seeker reassurance without
   forcing either to feel like the other.
5. **Trust is visible** — the citation is a first-class part of every answer, not a footnote.

## Accessibility & Inclusion

Audience includes distressed and low-focus users. Requirements: high legibility, calm low-arousal
visual language, clear reading order, keyboard navigation, visible focus, sufficient contrast in
light and dark, and respect for reduced-motion. Crisis resources must be unmissable.
