# Modular monolith with feature-based vertical slices

The backend is a **single deployable (a modular monolith)** organized into **feature modules**
(vertical slices), not by technical layer. Each feature owns its full stack — router, service,
schemas, models, repository, tests — under `app/features/<feature>/`. Cross-cutting infrastructure
(config, DB, Redis, the LiteLLM gateway, observability, security primitives) lives in a shared
`app/core/` platform layer that features depend on. Features depend on `core` and on explicitly
shared contracts, **never on another feature's internals**; cross-feature interaction goes through
a feature's public service interface.

## Why

- **One deployable, clear seams.** A modular monolith gives the operational simplicity of one
  service (one `docker compose up`, one Render container — [ADR-0003](0003-hybrid-deployment.md))
  with the internal boundaries of a well-factored system. No premature microservices.
- **Vertical slices match how the work is reasoned about.** "Auth", "conversations", "safety",
  "retrieval" are the units of the PRD and the `feature-dev` workflow. Grouping a feature's
  router+service+models together (instead of scattering them across `api/`, `services/`,
  `models/`) keeps a change local to one folder and makes the codebase legible to a reviewer.
- **Future-proof without over-building.** If any slice ever needs to become its own service, its
  boundary already exists; until then we pay none of the distributed-systems tax.

## Feature modules (initial)

`auth` · `conversations` · `chat` · `assistant` (LangGraph graph/nodes/state) · `retrieval`
(embeddings, pgvector, keyword tool) · `corpus` (documents, chunks, ingestion) · `safety` (crisis,
faithfulness judge, disclaimers) · `evals`. Shared platform: `core/` (config, db, redis, security,
`llm/` gateway, observability).

## Enforcing the boundaries (not just documenting them)

- **`import-linter`** contracts in CI: declare the layered/independent module rules and fail the
  build on a forbidden import (e.g. `features.safety` importing `features.auth` internals, or any
  feature importing another feature's `repository`).
- Ruff's `flake8-tidy-imports` banned-api to block deep cross-feature imports.
- A feature exposes a thin `__init__`/`service` public surface; everything else is internal.

## Trade-offs / consequences

- Some concepts (a shared `Answer`/`Citation` contract) genuinely span features and live in a
  `shared/` contracts module; deciding what is truly shared vs. duplicated is an ongoing judgment.
- The discipline only holds if the import contracts are actually run in CI; without them the slices
  erode into a big ball of mud. The CI contract is therefore part of this decision, not optional.
