---
id: 0006
title: Finalize Answer + citation contract detail
type: grilling
status: open
assignee:
blocked_by: []
---

## Question

Nail the exact shapes project.md sketches. The `category` enum values (which psychology/psychiatry
subfields), the `confidence` representation (enum low/med/high vs 0–1), and — most importantly —
how a **Citation** references source material: document id + chunk id + human-readable locator
(chapter/section/page), and how the synthesis model is made to emit citations that map to *actually
retrieved* chunks (not invented). Output: the final Pydantic models for `Answer`, `Citation`, and
the judge verdict.
