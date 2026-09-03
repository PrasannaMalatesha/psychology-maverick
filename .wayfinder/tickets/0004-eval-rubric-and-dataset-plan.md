---
id: 0004
title: Eval rubric + dataset plan
type: grilling
status: open
assignee:
blocked_by: []
---

## Question

Lock the offline eval design: the judge rubric and scoring scale for **faithfulness** and
**retrieval relevance** (binary vs 1–5 vs 0–1), the pass thresholds for the CI quality gate, the
size and composition of `evals/dataset.jsonl` (~25 questions spanning learning + clarity intents,
all three registers, plus at least a few `insufficient_context` and crisis cases), and the
build-then-verify process (LLM-drafted → human-labeled). Reuse the same judge model/rubric as the
runtime guardrail. Output: the rubric text, thresholds, and a dataset-construction checklist.
