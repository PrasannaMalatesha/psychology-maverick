# Spec — M7: Evals & CI quality gate

**Status:** draft · **Milestone:** M7 (Build Sequence §15.7) · **Last updated:** 2026-09-25
**Builds on:** M1–M6. **Respects:** project.md §12 (offline eval suite + CI quality gate), PRD FR-O2 and
success metrics (Faithfulness ≥ 0.8, retrieval relevance ≥ 0.8, CI green incl. security scans),
ADR-0004 (crisis-first — recall is non-negotiable), ADR-0002 (judge is a gateway role). Vocabulary per
[CONTEXT.md](../../CONTEXT.md): **Query, Answer, Corpus, Citation, Insufficient Context, Faithfulness,
Crisis Escalation**.

## Problem Statement

Answer quality is unmeasured. The test suite asserts structure and routing through a deterministic
`FakeGateway`, never whether Answers are faithful or retrieval finds the right passages. Nothing runs
automatically either: there is no CI, so ruff/pyright/import-linter/pytest are only as green as the
last person remembered to run them, and the security scans deferred from M6 (pip-audit, gitleaks,
Trivy) don't exist. The crisis matcher, the faithfulness judge's rubric, and `grounding_threshold`
(0.5, set from one live run) have never been checked against a labeled set.

## Solution

1. **CI quality gate** — a GitHub Actions workflow on push/PR to `dev`, `main`, `prod` running the
   existing gate (ruff lint + format check, pyright, import-linter, pytest over testcontainers
   Postgres) plus security scans (pip-audit, gitleaks, Trivy filesystem). Any failure fails the build.
2. **One eval runner, two modes**, over a labeled dataset (`evals/dataset.jsonl`, project.md §12):
   - **Deterministic** — fixture Corpus + `FakeGateway`, no keys, runs in CI on every push. Checks
     routing and retrieval outcomes exactly: Answer state per case (grounded / Insufficient Context /
     crisis), expected source in the top-k, crisis recall and precision.
   - **Live** — the real Corpus (`data/fetch_corpus.sh`), the real embedder, and the Gemini `judge`
     role. Scores Faithfulness and retrieval relevance against the PRD thresholds. Run on demand
     locally; in CI only when a `GEMINI_API_KEY` secret is configured (skipped otherwise).
3. **Calibrate what M4/M5 deferred**, driven by the live eval: the faithfulness rubric, the
   `grounding_threshold`, and the crisis phrase list.

The eval uses the **same** `ModelGateway.is_faithful` the runtime judge uses — one rubric, one source
of truth (project.md §12).

## User Stories

1. As a developer, every push shows a green/red CI check covering lint, types, module boundaries, tests,
   evals, and security scans.
2. As a developer, I can run the eval suite with one command and get a per-metric report and a non-zero
   exit when a threshold fails.
3. As the owner, a change that makes the assistant miss a crisis Query fails CI (crisis recall must be
   1.0 — ADR-0004).
4. As the owner, with a Gemini key I can measure Faithfulness and retrieval relevance on the real Corpus
   and see them against the 0.8 targets.
5. As the owner, `grounding_threshold` and the judge rubric are set from eval evidence, not guesses.
6. As a Reviewer (portfolio), I can read the eval dataset, the thresholds, and the CI run.

## Implementation Decisions

- **Workflow runs from `backend/`** with `uv`; GitHub-hosted Ubuntu runners have Docker, so
  testcontainers works unchanged. The 9 files currently drifting from `ruff format` are formatted once
  so the format check can join the gate.
- **Security scans:** `pip-audit` against the locked dependency set; `gitleaks` over git history;
  Trivy filesystem scan failing on HIGH/CRITICAL. Any finding the scans raise is fixed or explicitly
  ignored with a reason in the ticket.
- **Dataset:** JSONL, one case per line: the Query, the expected Answer state, and (for grounded cases)
  the expected source(s). Deterministic cases target the fixture Corpus; live cases target the real
  Corpus. The live set (~25 Queries across all three registers, plus Insufficient Context and crisis
  cases) is drafted by the implementer and **labels are verified by the owner** (project.md §12:
  "LLM-drafted then human-labeled").
- **Deterministic mode asserts exact outcomes** (the fake is deterministic, so any drift is a
  regression). It runs inside the existing pytest run, reusing the testcontainers database, so CI needs
  no extra service for it.
- **Live thresholds** (PRD §8): Faithfulness ≥ 0.8, retrieval relevance ≥ 0.8; crisis recall = 1.0 in
  both modes.
- **Crisis detection stays a deterministic phrase matcher**, widened by eval misses (indirect phrasing,
  typos) while keeping false positives (e.g. research questions about suicide rates) visible in the
  report. A model-based crisis classifier is **not** built in M7 — only if the phrase list cannot reach
  recall 1.0.
- **Faithfulness rubric:** tuned against live eval cases that include deliberately unfaithful Answers,
  so the judge's ability to catch them is measured, not assumed.

## Testing Decisions

- The deterministic eval is itself a pytest test over the dataset, so it can't silently rot.
- The runner's scoring logic (metric aggregation, threshold pass/fail, exit code) is covered offline.
- Live mode is never required for the PR gate — it depends on a secret and network access.

## Out of Scope (deferred)

- **Per-passage Category classifier** — deferred past M7 (owner decision, 2026-09-25). The per-register
  default already routes clinical content to the disclaimer.
- Model-based crisis classifier (see above).
- Tool-selection eval (project.md §12: "once the graph is stable").
- Langfuse-hosted eval runs / dashboards (M9 wires Langfuse Cloud).
- Rate-limiting, audit logging, PII-hashing, production `JWT_SECRET` enforcement at startup (M9).

## Further Notes

- Only a Gemini key is available; the live judge is `gemini/gemini-1.5-flash` via the `judge` role.
- The M4–M6 code review (2026-09-25) fixed a multi-turn stale-answer regression that the old tests
  missed because they asserted history counts, not content — a concrete argument for M7's
  outcome-level evals.
