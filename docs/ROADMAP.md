# Build Roadmap — Psychology Maverick

**A living tracker so the 9 build milestones never get lost.** Update the Status column as work lands.

- **Plan / source of truth:** [project.md §15](../project.md) (build sequence), [docs/PRD.md](PRD.md) (product), [docs/adr/](adr/) (decisions), [CONTEXT.md](../CONTEXT.md) (glossary).
- **How milestones get built:** each one gets its own spec via `/to-spec` → filed as a GitHub issue with the `ready-for-agent` label → built → checked off here. One spec = one buildable slice; there is intentionally **no single spec for the whole app**.
- **Status legend:** ⬜ not started · 🟡 spec written · 🔵 in progress · ✅ done

| M | Milestone | Scope (one line) | Spec | Issue | Status |
|---|-----------|------------------|------|-------|:---:|
| **M1** | Vertical slice | Ingest a corpus *subset* → real `POST /chat` (retrieve → synthesize) → one Langfuse trace. Proves the spine. | [M1-rag-chat-slice.md](specs/M1-rag-chat-slice.md) | — | 🟡 |
| **M2** | Contracts & storage | Full `Answer` Pydantic contract, complete Postgres schema + pgvector/HNSW, full ingestion CLI over the whole corpus. | — | — | ⬜ |
| **M3** | Agent | LangGraph node graph, tool-calling (keyword/fetch), Postgres checkpointer, multi-turn conversations. | — | — | ⬜ |
| **M4** | Safety *(non-negotiable — [ADR-0004](adr/0004-informational-safety-posture.md))* | Crisis-escalation node (before retrieval), faithfulness judge, human-in-the-loop interrupt, clinical disclaimers. **Gate: no user-facing launch before this.** | — | — | ⬜ |
| **M5** | Model gateway | LiteLLM registry, role-based routing + fallback across the full model set ([ADR-0002](adr/0002-config-driven-model-gateway.md)). | — | — | ⬜ |
| **M6** | Auth & security | Email+password JWT (argon2, refresh rotation, Redis revocation), user/admin RBAC, per-User conversation ownership. | — | — | ⬜ |
| **M7** | Evals & CI gate | Offline evaluation suite (faithfulness, retrieval quality) + CI quality gate + `import-linter` boundary checks. | — | — | ⬜ |
| **M8** | Frontend | Chat + citations + trust states + auth + sidebar, on the chosen frontend (see open decision below). | — | — | ⬜ |
| **M9** | Deploy | Compose → Render (FastAPI) + Neon (Postgres) + Upstash (Redis) + Vercel + Langfuse Cloud ([ADR-0003](adr/0003-hybrid-deployment.md)). | — | — | ⬜ |

**Definition of v1 / MVP:** M1–M9 together — a real User can sign in, ask a Query, and get a safe, grounded, cited Answer in a deployed UI. M1 alone is an *internal spine proof*, not a shippable product.

## Open decisions (resolve before the milestone they block)

- **Frontend target (blocks M8):** the ADRs assume a **Next.js** app on the **MindMarket** design system (this canonical repo). The polished session work lives on a **divergent fork** (Vite/React, DM fonts, DSM-5 + freemium + editorial redesign). Decide whether M8 builds the canonical Next.js frontend or adopts/ports the fork. The M1–M7 backend is frontend-agnostic, so this does not block them.
- **Provisioning (blocks M9, partially M1 dev):** Neon is reachable via connector; Upstash, Langfuse, Render, Vercel accounts are the owner's task.

## Progress log

- **2026-09-03** — Repo scaffolded + pushed to GitHub (`PrasannaMalatesha/psychology-maverick`, public). Agent-skill config + triage labels set up. M1 spec written. Backend not yet built; canned matcher still in place.
