---
id: 0002
title: Structure-aware chunking strategy decision
type: grilling
status: open
assignee:
blocked_by: [0001]
---

## Question

Given the parser choice, lock the concrete chunking rules: target chunk size and overlap, how
section/chapter boundaries are detected per register (textbook vs article vs brochure), what
`section_metadata` is captured for citations, and how figures/tables/references are handled or
dropped. Output a spec precise enough to implement `rag/chunking.py` without further decisions.
