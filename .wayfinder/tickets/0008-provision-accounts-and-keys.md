---
id: 0008
title: Provision external accounts + keys
type: task
status: open
assignee:
blocked_by: []
---

## Question

(Task — HITL, user-performed.) Stand up the external services the design depends on so their
config can be wired: **Neon** (Postgres+pgvector), **Upstash** (Redis), **Langfuse Cloud**,
**Render** (backend), **Vercel** (frontend). Confirm the existing **Gemini API key**. Nothing to
decide — the discussion is unblocked once these exist. Resolution records where each secret lives
(in `.env`, never committed) and any URLs/IDs later work depends on. The agent scaffolds
`.env.example` and wiring; the user creates accounts and pastes real secrets (agent never enters
credentials or creates accounts on the user's behalf).
