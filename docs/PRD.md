# PRD — Psychology Maverick

**Status:** Draft for build sign-off · **Owner:** solo · **Last updated:** 2026-08-27
**Companion docs:** [project.md](../project.md) (engineering spec) · [CONTEXT.md](../CONTEXT.md)
(glossary) · [ADRs](adr/) · [wayfinder map](../.wayfinder/MAP.md) (open decisions)

> This PRD states *what* we are building and *why*, and the bar for "done." The *how* lives in
> project.md. Where a requirement still depends on an open decision, it is tagged
> **[OPEN → ticket]** and linked to the wayfinder ticket that will close it.

---

## 1. Summary

A retrieval-grounded AI assistant that answers questions about **psychology, psychiatry, and
mental health** from a curated, openly-licensed corpus, citing every claim back to its source. It
serves two audiences under one safe, informational posture: **learners** exploring the fields, and
**people seeking clarity** about a mental-health topic. It is built as a **portfolio-grade
production system** — the LLM is a small part; the engineering around it (safety, retrieval,
observability, evals, security) is the point.

---

## 2. Problem

- **General-purpose chatbots hallucinate** on psychology/psychiatry and cite nothing, so answers
  can't be trusted or verified — dangerous for a domain where wrong information causes real harm.
- **Authoritative material is scattered and dense** (textbooks, research papers, clinical
  brochures); a learner or worried person can't easily get a grounded, plain-language answer with
  a source they can check.
- **Most "AI apps" are demos**, not systems — no safety design, no evals, no observability, no
  security. There's a gap between "calls an LLM" and "trustworthy application."

---

## 3. Goals & Non-Goals

### Goals
1. Answer psychology/psychiatry/mental-health questions **grounded in the corpus, with citations**.
2. Be **safe by construction** for a vulnerable audience: crisis-first, informational-only.
3. Serve **both learning and clarity** intents with an appropriate register and tone.
4. Demonstrate a **complete production stack** (FastAPI, LangGraph, Postgres+pgvector, Redis,
   LiteLLM, Langfuse, evals, auth/security, CI, deploy) as a portfolio artifact.
5. Be **reproducible and runnable** by a reviewer (`docker compose up`, one-command corpus fetch).

### Non-Goals
- Not a diagnostic, therapeutic, or crisis-intervention service.
- Not personalized medical/mental-health advice.
- Not a general-knowledge assistant (answers only from the curated corpus).
- Not covering cloud infra concerns beyond a single deploy (K8s, autoscaling — see project.md §16).

---

## 4. Users & Personas

| Persona | Who | Primary need |
|---------|-----|--------------|
| **The Learner** | Student / curious person exploring psychology or psychiatry | Accurate, cited explanations at academic depth; "what does research say about X?" |
| **The Clarity-Seeker** | Someone trying to understand a mental-health topic for themselves or a loved one | Plain-language, reassuring, authoritative info; "what are the signs of depression?" |
| **The Admin** | Corpus maintainer (project owner) | Ingest/refresh corpus, see corpus stats |
| **The Reviewer** *(meta)* | Interviewer / hiring manager evaluating the portfolio | Clone, run, read the code, see the engineering maturity |

---

## 5. Key Use Cases / User Stories

1. *As a Learner*, I ask "How does classical conditioning differ from operant conditioning?" and
   get a grounded answer citing the textbook chapter, so I can verify and read more.
2. *As a Clarity-Seeker*, I ask "What are the symptoms of generalized anxiety?" and get a
   plain-language answer sourced from NIMH, with a clear "informational, not a diagnosis" note.
3. *As either user*, I ask a **follow-up** ("and how is it treated?") and the assistant remembers
   the conversation.
4. *As a user in distress*, I express suicidal intent, and the assistant **does not attempt a
   corpus answer** — it surfaces crisis resources immediately.
5. *As a user asking outside the corpus* ("what's the weather?"), I get an honest
   `insufficient_context` response, not a hallucination.
6. *As an Admin*, I run the ingestion CLI to (re)build the index and view corpus stats.
7. *As a Reviewer*, I clone the repo, run `docker compose up` + the corpus fetch, and use the app
   locally; I read a Langfuse trace and the eval results in CI.

---

## 6. Functional Requirements

### 6.1 Corpus & Ingestion
- **FR-C1** Corpus is curated, openly-licensed, three registers (textbook, research, consumer
  health), covering psychology **and** psychiatry. *(Done — see [SOURCES.md](../data/corpus/SOURCES.md).)*
- **FR-C2** Ingestion is an **offline CLI** that parses PDFs → structure-aware chunks → embeddings
  → Postgres. **[OPEN → [PDF parsing + chunking][t1] / [chunking strategy][t2]]**
- **FR-C3** Every chunk carries `register`, `topic`, and section metadata for citations.
- **FR-C4** Corpus is reproducible via `data/fetch_corpus.sh`. *(Done.)*

### 6.2 Retrieval & Answering
- **FR-R1** Default retrieval: semantic top-k=5 over pgvector (HNSW).
- **FR-R2** A **keyword/fetch-document tool** is the escape hatch when semantic retrieval is weak
  or the query is an exact-term lookup.
- **FR-R3** Answers are **grounded**: claims trace to retrieved chunks.
- **FR-R4** Structured output (`Answer`): `answer`, `citations[]`, `confidence`,
  `insufficient_context`, `category`. **[OPEN → [Answer + citation contract][t6]]**
- **FR-R5** **Register preference**: personal/clarity queries prefer NIMH; academic queries prefer
  textbook/research. Every answer states its source.
- **FR-R6** On no coverage, return `insufficient_context` rather than inventing an answer.

### 6.3 Conversation
- **FR-V1** Multi-turn: conversation history persists in Postgres per user.
- **FR-V2** LangGraph checkpointer holds resumable thread state.
- **FR-V3** Users can list / switch / rename / delete their own conversations.

### 6.4 Safety *(critical — see [ADR-0004](adr/0004-informational-safety-posture.md))*
- **FR-S1** **Crisis detection runs first**; on acute-risk signals it surfaces crisis resources
  (default US 988 + findahelpline.com, region-configurable) and stops — no corpus answer.
  **[OPEN → [Crisis-detection mechanism][t3]]**
- **FR-S2** **Faithfulness judge** (runtime): checks groundedness before an answer ships; on
  failure → retry once → else `insufficient_context`. Toggleable.
- **FR-S3** **Human-in-the-loop** interrupt for low-confidence clinical answers.
- **FR-S4** **Clinical disclaimer** on clinical-category answers.
- **FR-S5** Informational-only: never diagnoses or gives personalized treatment advice.

### 6.5 Accounts & Access
- **FR-A1** Email/password auth; JWT access + refresh with rotation; argon2 hashing.
- **FR-A2** RBAC: `user` and `admin`. Users access **only their own** conversations (enforced in
  the data layer).
- **FR-A3** Admin-only: ingestion trigger context + corpus-stats view.

### 6.6 Model Gateway
- **FR-M1** All model calls go through a **config-driven LiteLLM registry**; any provider pluggable
  by config + key. **[OPEN → [LiteLLM role→model config][t7]]**
- **FR-M2** Role-based routing (cheap grader/judge, premium synthesizer) + fallback chains.
- **FR-M3** Embeddings config-driven; default local `bge-small-en-v1.5` (384-dim).

### 6.7 Observability & Evals
- **FR-O1** Langfuse traces every graph step.
- **FR-O2** Offline eval suite (LLM-as-judge) scores faithfulness + retrieval relevance; runs as
  `make eval` and in CI with a quality gate. **[OPEN → [Eval rubric + dataset][t4]]**

### 6.8 Frontend
- **FR-F1** Next.js app: streaming chat, conversation sidebar, auth pages, expandable **citation
  UX**, trust/safety states (insufficient-context, confidence, disclaimer, crisis card).
  **[OPEN → [Design system][t5]]**
- **FR-F2** Calm-editorial design, matched to a mental-health audience.

### 6.9 Deployment
- **FR-D1** Local: `docker compose up`. Prod: Vercel (frontend) → Render (backend) → Neon +
  Upstash + Langfuse Cloud. **[OPEN → [Provision accounts][t8]]**

---

## 7. Non-Functional Requirements

- **Performance:** fully async path; HNSW index; connection pooling; embedding model loaded once;
  SSE streaming; Redis response/embedding cache. Target: p95 answer-start < 2s on warm cache
  (excludes cold starts).
- **Security:** argon2, JWT+rotation+revocation, RBAC + per-user ownership, parameterized SQL,
  CORS allow-list, security headers, `.env` hygiene, request/query caps, login brute-force
  protection, audit logging, PII-aware tracing, DB least-privilege, CI scanning (pip-audit,
  gitleaks, Trivy). *(Full list: [project.md §9](../project.md).)*
- **Reliability:** provider fallback via LiteLLM; graceful `insufficient_context`; crisis path
  independent of retrieval.
- **Cost:** free-tier friendly (local embeddings, Gemini, free managed tiers).
- **Accessibility:** WCAG-minded — keyboard nav, focus states, contrast in light/dark, respects
  reduced-motion.
- **Maintainability:** `uv` + `ruff`, typed Pydantic contracts, ADRs, tests.
- **Reproducibility:** one-command corpus fetch + `docker compose up`.

---

## 8. Success Metrics

**Product/quality**
- **Faithfulness** ≥ 0.8 on the eval set (CI gate).
- **Retrieval relevance** ≥ 0.8 on the eval set.
- **Crisis handling:** 100% of crisis test cases route to resources (no corpus answer) — zero
  tolerance for misses.
- **Hallucination:** out-of-corpus questions return `insufficient_context`, not an invented answer.

**Engineering (portfolio signal)**
- Reviewer can run locally in one command; a Langfuse trace is visible.
- CI green: lint, tests, evals gate, security scans.
- Every hard-to-reverse decision has an ADR.

---

## 9. Scope & Milestones (MVP-first)

| Milestone | Outcome | Maps to |
|-----------|---------|---------|
| **M0 Plan** | PRD + decision-complete plan (this map cleared) | wayfinder tickets |
| **M1 Vertical slice** | Subset ingest → `/chat` retrieve→synthesize → visible Langfuse trace | project.md §15.1 |
| **M2 Contracts & storage** | Pydantic `Answer`, full schema + pgvector/HNSW, full ingestion CLI | §15.2 |
| **M3 Agent** | LangGraph nodes + tool branch + checkpointer + multi-turn | §15.3 |
| **M4 Safety** | Crisis node, faithfulness judge, HITL, disclaimers | §15.4 |
| **M5 Gateway** | LiteLLM registry + routing + fallback | §15.5 |
| **M6 Auth & security** | Full auth + hardening checklist | §15.6 |
| **M7 Evals** | Suite + CI quality gate | §15.7 |
| **M8 Frontend** | Chat + citations + trust states + auth + sidebar | §15.8 |
| **M9 Deploy** | Render + Neon + Upstash + Vercel + Langfuse Cloud | §15.9 |

---

## 10. Dependencies & Assumptions

- **Available now:** a Google **Gemini API key**. Claude Pro is a chat subscription, **not** API
  access; adding Claude/OpenAI/OpenRouter later is a config change (LiteLLM).
- **To provision:** Neon, Upstash, Langfuse Cloud, Render, Vercel *([Provision accounts][t8])*.
- **Assumes** local machine can run `torch`/`bge` for offline embedding and a Render container can
  at runtime.
- **Legal:** all corpus sources openly licensed; non-commercial (textbook is NC).

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Harmful/incorrect mental-health output** | High | Informational posture, faithfulness judge, HITL, disclaimers, crisis-first ([ADR-0004](adr/0004-informational-safety-posture.md)) |
| **Missed crisis signal** | Severe | Conservative detection biased to false-positives; dedicated crisis test cases at 100% |
| **Hallucinated citations** | High | Citations must map to retrieved chunks; judge verifies groundedness *([t6])* |
| **Poor retrieval on dense/multi-column PDFs** | Medium | Structure-aware chunking; parser evaluation *([t1]/[t2])* |
| **Scope creep** (solo, ~1–2 wk) | Medium | MVP-first; future-work explicitly deferred (project.md §16) |
| **Free-tier limits / cold starts** | Low | Documented; cron-ping or paid tier |
| **Single provider today** | Low | Registry + fallback ready; degrades gracefully *([t7])* |

---

## 12. Open Questions (tracked as wayfinder tickets)

- [PDF parsing + chunking library landscape][t1] · [Structure-aware chunking strategy][t2]
- [Crisis-detection mechanism][t3]
- [Eval rubric + dataset plan][t4]
- [Calm-editorial design system][t5]
- [Answer + citation contract detail][t6]
- [LiteLLM role→model config][t7]
- [Provision external accounts][t8] · [Repo scaffolding + CI][t9]

---

## 13. References

[project.md](../project.md) · [CONTEXT.md](../CONTEXT.md) · [ADRs](adr/) ·
[SOURCES.md](../data/corpus/SOURCES.md) · [wayfinder map](../.wayfinder/MAP.md)

[t1]: ../.wayfinder/tickets/0001-pdf-parsing-chunking-library-landscape.md
[t2]: ../.wayfinder/tickets/0002-chunking-strategy-decision.md
[t3]: ../.wayfinder/tickets/0003-crisis-detection-mechanism.md
[t4]: ../.wayfinder/tickets/0004-eval-rubric-and-dataset-plan.md
[t5]: ../.wayfinder/tickets/0005-frontend-design-system.md
[t6]: ../.wayfinder/tickets/0006-answer-citation-contract-detail.md
[t7]: ../.wayfinder/tickets/0007-litellm-role-model-config.md
[t8]: ../.wayfinder/tickets/0008-provision-accounts-and-keys.md
[t9]: ../.wayfinder/tickets/0009-repo-scaffolding-decision.md
