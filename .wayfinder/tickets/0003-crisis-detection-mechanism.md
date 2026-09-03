---
id: 0003
title: Crisis-detection mechanism
type: grilling
status: open
assignee:
blocked_by: []
---

## Question

How does the first-node crisis check actually decide a query signals acute risk? Choose between a
curated lexicon/regex, a small LLM classifier, or a hybrid (fast lexical pre-filter → LLM confirm).
Define: the risk signals in scope (self-harm, suicidal intent, harm to others?), the
false-negative vs false-positive posture (we bias toward showing resources), the exact
crisis-response payload (message + resources), region handling (default US 988 + findahelpline.com),
and how the mechanism is tested. This is the highest-stakes decision on the map
([ADR-0004](../../docs/adr/0004-informational-safety-posture.md)); a prototype of the classifier
on sample queries may be warranted.
