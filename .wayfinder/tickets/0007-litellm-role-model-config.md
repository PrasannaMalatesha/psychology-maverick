---
id: 0007
title: LiteLLM role→model config + fallbacks
type: grilling
status: open
assignee:
blocked_by: []
---

## Question

Given only a Gemini API key today (Claude Pro is not API access), pin the concrete registry: exact
model IDs for `grader`, `synthesizer`, `judge`, `embedder`, plus fallback ordering and how the app
degrades when only one provider is configured. Confirm local `bge-small-en-v1.5` as the default
embedder and the Gemini-embeddings switch. Output: the committed `models.yaml` (or equivalent) with
sane defaults and documented env keys ([ADR-0002](../../docs/adr/0002-config-driven-model-gateway.md)).
