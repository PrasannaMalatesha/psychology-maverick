# Knowledge Assistant

A retrieval-grounded agent that answers questions from a curated body of psychology, psychiatry, and mental-health source material and cites where each answer came from. Dual-purpose: a **learning** companion for psychology and psychiatry, and a **clarity** tool for mental health — always informational (never diagnosis or personalized advice), safe by construction. Built as a portfolio-grade demonstration of a production AI application stack.

## Language

**Knowledge Assistant**:
The agent/application as a whole — it receives a query, retrieves relevant material, and produces a grounded, cited answer.
_Avoid_: bot, chatbot, model

**Query**:
A single question a user asks the assistant.
_Avoid_: prompt, request, message

**Answer**:
The assistant's response to a query — grounded in the corpus, not free invention.
_Avoid_: completion, output, response

**Corpus**:
The body of source material the assistant is allowed to answer from, in three registers: the OpenStax *Psychology 2e* textbook (foundational), PLOS ONE psychology research articles (current research), and NIMH mental-health brochures (authoritative consumer health info). See [data/corpus/SOURCES.md](data/corpus/SOURCES.md).
_Avoid_: dataset, knowledge base, documents

**Citation**:
A reference from an answer back to the specific corpus passage that supports it.
_Avoid_: source, reference, link (as bare terms)

**Category**:
The psychology subfield an answer belongs to (e.g. cognitive, social, clinical, developmental) — a fixed enum, used to tag answers and slice evaluations.
_Avoid_: topic, tag, subject

**Insufficient Context**:
The state where the corpus does not cover a query, and the assistant declines to answer rather than inventing one. The correct behaviour when grounding is impossible.
_Avoid_: "don't know", failure, no-answer

**User**:
An authenticated person who queries the assistant. Owns their own conversations and can see no one else's.
_Avoid_: account, client, member

**Admin**:
A privileged role that manages the corpus (ingestion, corpus stats) and can see system-level data. Not a super-user over other users' conversations.
_Avoid_: superuser, root, owner

**Faithfulness**:
The property that every claim in an answer is grounded in the retrieved corpus passages — not invented. The primary quality the runtime judge and the offline evals measure.
_Avoid_: accuracy, correctness, truthfulness

**Crisis Escalation**:
The path taken when a query signals acute risk (e.g. self-harm, suicidal intent). The assistant does **not** try to answer from the corpus; it surfaces crisis-support resources (e.g. a helpline) and a safety message. Takes priority over normal retrieval.
_Avoid_: emergency mode, red-flag, block
