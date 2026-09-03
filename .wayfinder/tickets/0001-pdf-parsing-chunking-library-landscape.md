---
id: 0001
title: PDF parsing + chunking library landscape
type: research
status: open
assignee:
blocked_by: []
---

## Question

Across three PDF formats (OpenStax textbook, PLOS article two-column layout, NIMH brochures),
what are the real options for text extraction + structure detection, and their trade-offs?
Compare at least PyMuPDF, pdfplumber, `unstructured`, and a hosted parser (e.g. LlamaParse):
extraction quality on multi-column PLOS PDFs, ability to recover headings/sections for citation
metadata, dependency weight (must fit a Render container), speed, and license/cost. Surface a
recommendation for the chunking-strategy decision to build on.
