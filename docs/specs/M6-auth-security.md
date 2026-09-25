# Spec — M6: Auth & security (JWT, RBAC, per-User ownership)

**Status:** draft · **Milestone:** M6 (Build Sequence §15.6) · **Last updated:** 2026-09-25
**Builds on:** M1–M5. **Respects:** project.md §9 (security controls), ADR-0003 (Upstash Redis), ADR-0005/0006 (feature slices + seams). Vocabulary per [CONTEXT.md](../../CONTEXT.md): a **User** owns their conversations and sees no one else's; an **Admin** manages the corpus, not other users' data.

## Problem Statement

Every endpoint is unauthenticated. Anyone can call `/chat`, read any `GET /conversations/{id}`, or
resume any review — there is no User, no login, and no data ownership (a textbook OWASP-API #1 IDOR
hole). project.md §9 locks argon2 + JWT (access/refresh with rotation) + `user`/`admin` RBAC +
strict per-user ownership before any user-facing launch.

## Solution

Add an `auth` feature (the foundational layer — every feature may depend on it, it depends on none):
Users register with an email + argon2-hashed password and log in for a signed JWT **access** token
(short-lived, carries id + role) and a **refresh** token (rotated on use, revocable). A `current_user`
dependency guards protected routes (401 on missing/invalid); conversations are owned by their creator
and reading/resuming another User's conversation is 403; an `admin`-only corpus-stats route
demonstrates RBAC. Refresh-token revocation is a seam — in-memory by default, Redis in production.

## User Stories

1. As a person, I can register and log in, and receive tokens that authenticate my later requests.
2. As a User, my conversations are mine: no one else can read or continue them.
3. As a User, I stay logged in via refresh without re-entering my password; logging out invalidates my refresh token.
4. As an Admin, I can see corpus stats; a regular User cannot.
5. As a developer, I can exercise the whole thing offline (real Postgres, FakeGateway, in-memory revocation) with no live Redis or provider keys.
6. As a developer, non-HTTP service callers keep working without a user, so M1–M5 tests are unaffected.

## Implementation Decisions

- **`auth` is the bottom import-linter layer** `[chat, assistant, retrieval, corpus, auth]`: features
  may import `auth` (chat does, for `current_user`); `auth` imports only `core`.
- **Persistence in `core.store`** (same `Base`, created by `init_store`): a `users` table and a
  `conversation_owners` map (`conversation_id → user_id`, first-writer-wins via
  `ON CONFLICT DO NOTHING`). Keeps all DDL in one bootstrap, matching `Passage`.
- **argon2-cffi** for hashing, **PyJWT** for tokens — both promoted to *core* dependencies (auth is
  core now), not extras. Access token: `sub`+`role`+`exp` (role travels in the token, no DB hit to
  authorize). Refresh token: `sub`+`jti`+`exp`; rotation revokes the old `jti` and issues a new pair.
- **Revocation seam** (`auth.security`): `InMemoryRevocationStore` default; `RedisRevocationStore`
  (lazy, optional `redis` extra) when `redis_url` is set. Same pattern as the MemorySaver checkpointer
  and the model-gateway adapters — tests need no live Redis.
- **Non-breaking rollout (expand-then-enforce):** `ChatService` gained an optional `engine` and
  `user_id` (both last/keyword), so existing positional/service-level callers are unchanged and record
  no ownership; the HTTP layer always supplies a user and enforces ownership. The shared test `client`
  fixture registers+logs in once, so existing HTTP tests run authenticated with no behaviour change.
- **RBAC:** `require_admin` gates `GET /admin/corpus-stats` (composition-root route). Registration
  only ever mints `user`; an `admin` is seeded through the service (a real admin-provisioning flow is
  out of scope).
- **Cheap always-on §9 controls added now:** CORS allow-list (configurable; the Vercel origin at
  deploy) and a security-headers middleware (`nosniff`, `DENY`, `no-referrer`).

## Testing Decisions

- Over the HTTP seam against real Postgres, FakeGateway the only stub; each auth test builds its own
  app so token/ownership state is isolated. Covers: register/login, duplicate-email 409, wrong-password
  401, unauthenticated/garbage-token 401, `/health` public, refresh rotation + reuse-rejected, logout
  revocation, admin 403-vs-200, and the IDOR case (a second User gets 403 on another's conversation).
- All M1–M5 tests stay green; only the shared `client` fixture and one self-built client gained a login.

## Out of Scope (deferred to M7 / M9)

- Rate-limiting / login brute-force protection, auth-event audit logging, PII-hashing before Langfuse
  (all need Redis / the tracing pipeline).
- CI security scanning (`pip-audit`, `gitleaks`, `Trivy`), httpOnly-cookie refresh + CSRF, HSTS/WAF —
  deploy-tier (M9) and CI (M7).
- A self-service admin-provisioning flow and password reset/email verification.
- Live Redis-backed revocation verification (only the in-memory path is exercised; the Redis adapter
  is wired but unused until provisioned — ADR-0003).

## Further Notes

- New runtime deps: `argon2-cffi`, `pyjwt`. Optional `redis` extra for the production revocation store.
- The dev `jwt_secret` default is a placeholder ≥32 bytes; production MUST set `JWT_SECRET`.
