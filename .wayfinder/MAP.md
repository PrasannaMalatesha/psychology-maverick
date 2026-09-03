---
label: wayfinder:map
tracker: local-markdown
---

# Map: Ship the Psychology & Psychiatry Knowledge Assistant

> **Local-markdown tracker conventions.** This file is the map. Tickets are files in
> `.wayfinder/tickets/NNNN-slug.md`, each with frontmatter: `id`, `title`, `type`
> (`research`|`prototype`|`grilling`|`task`), `status` (`open`|`closed`), `assignee`
> (empty = unclaimed), `blocked_by` (list of ticket ids). A ticket is **unblocked** when every
> id in `blocked_by` is closed. The **frontier** = open + unblocked + unassigned tickets.
> Refer to tickets by their **title**, never a bare number.

## Destination

A **correct PRD** ([docs/PRD.md](../docs/PRD.md)) plus a **decision-complete plan**: every
remaining open decision resolved so implementation can proceed phase-by-phase (per
[project.md §15](../project.md)) without stopping to decide. This map is done when no open
decision tickets remain and the PRD reflects them.

## Notes

- **Plan, don't do.** Tickets resolve *decisions*; building is handed to `feature-dev` (with
  `ponytail` overlaid) after the map clears. The build *phases* are the PRD roadmap, not tickets.
- **The design is already locked.** Do not re-litigate what [project.md](../project.md), the
  [ADRs](../docs/adr/), and [CONTEXT.md](../CONTEXT.md) settle. Tickets cover only what those
  leave open.
- **Skills to consult:** `grilling` + `domain-modeling` for decision tickets; `research` for
  research tickets; `prototype` for design/behavior tickets. Domain: a safety-critical,
  informational RAG assistant over psychology/psychiatry/mental-health.
- **Safety is non-negotiable** ([ADR-0004](../docs/adr/0004-informational-safety-posture.md)):
  informational-only, crisis-first. Any ticket touching answers or UX inherits this.

## Decisions so far

<!-- Seeded from the pre-map design grill; detail lives in the linked docs, not here. -->

- **Domain, corpus, agent shape, storage, models, safety posture, auth, deploy, frontend** —
  all settled in [project.md](../project.md) and recorded where hard-to-reverse in the
  [ADRs](../docs/adr/). This map does not restate them; it resolves what remains.

## Not yet specified

<!-- Fog: in-scope, not yet sharp enough to ticket. Graduates as the frontier advances. -->

- **Prompt library** — exact system prompts for synthesis, the faithfulness judge, and query
  understanding. Graduates once the Answer contract and crisis mechanism are locked.
- **Answer-quality tuning loop** — reranking / semantic-cache thresholds, top-k tuning. Blocked
  on having a working retrieval path + eval numbers to tune against.
- **Admin/corpus-stats surface detail** — depends on the frontend design system landing first.
- **CI pipeline detail** — exact jobs/gates. Depends on the repo-scaffolding decision.

## Out of scope

<!-- Ruled beyond this destination. Never graduates. -->

- Actually *building/deploying* the app — that's the post-plan `feature-dev` effort, not this map.
- Everything in [project.md §16](../project.md) future-work (K8s, OAuth, reranking, semantic
  cache, WAF, cookie-auth+CSRF).
