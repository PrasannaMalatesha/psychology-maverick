# Hybrid deployment: Vercel frontend + Render container backend

The frontend (Next.js) deploys to **Vercel**; the FastAPI backend deploys as a **Docker container
on Render**; data lives on **Neon** (Postgres+pgvector) and **Upstash** (Redis), with **Langfuse
Cloud** for tracing. Not all-Vercel-serverless, and not all-one-platform.

## Why

- The backend has heavy, stateful, long-running parts (LangGraph, local `torch`/`bge` embeddings,
  streaming, Postgres checkpoints) that fight Vercel's serverless limits (bundle size, execution
  time, no persistent process). A container is the natural home — and `docker-compose` ports to
  Render almost 1:1.
- Running the backend as a container **preserves local embeddings** (`bge`), avoiding a forced
  switch to API embeddings that pure-Vercel would have required.
- Vercel is still the best host for the frontend, giving a polished, clickable demo URL.

## Considered alternatives

- **All-in on Vercel (serverless Python):** would force Gemini embeddings and constant fighting of
  cold starts and function limits. Rejected for this stack.
- **All-container (Railway/Fly/Render for everything incl. frontend):** fine, but gives up Vercel's
  frontend DX and preview deployments.

## Consequences

- Two deploy targets to wire (CORS allow-list, env, CI). 
- **Do not use Render's free Postgres** (deleted after 30 days) — Neon holds the data.
- Render free web services cold-start after idle; mitigate with a cron ping or a paid tier.
