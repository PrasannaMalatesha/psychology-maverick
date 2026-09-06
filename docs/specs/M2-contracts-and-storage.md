# Spec — M2: Contracts & Storage (complete the ingestion + Answer layer)

**Status:** draft · **Milestone:** M2 (Build Sequence §15.2) · **Last updated:** 2026-09-06
**Builds on:** M1 ([M1-rag-chat-slice.md](M1-rag-chat-slice.md)). **Respects:** ADR-0001, ADR-0002, ADR-0005, ADR-0006. Vocabulary per [CONTEXT.md](../../CONTEXT.md).

## Problem Statement

M1 proved the spine on a *subset*: it ingests markdown + PDF, stores passages in pgvector, and
answers `POST /chat`. But the storage-and-contracts layer is not yet complete: the PLOS research
articles ship as **JSON** (an unsupported format, so part of the Corpus can't be ingested); passages
from PDFs carry **no Category** (so grounded Answers over them return `category: null`); the `Answer`
contract has **no invariants** (a `grounded` Answer with zero Citations is constructable); and there
is **no way to see what the Corpus contains** after ingestion.

## Solution

Complete the layer so the *whole* Corpus ingests and the contract is self-enforcing:

- Ingest all three registers in their real formats — add the **JSON** reader for PLOS articles — and
  attach a **Category** to every passage (from front matter, a per-source manifest, or a default per
  register), so full-corpus ingestion works end to end.
- Make the **`Answer` contract enforce its own shape** (grounded ⇒ text + ≥1 Citation + Category;
  Insufficient Context ⇒ no text/Category/Citations), so an ill-formed Answer cannot be constructed.
- Provide **corpus statistics** (documents and passages per register) so ingestion is verifiable.

## User Stories

1. As an Admin, I want to ingest the PLOS research articles from their JSON form, so that the research register is actually part of the Corpus.
2. As an Admin, I want to ingest the entire Corpus (all registers, all formats) in one command, so that the assistant answers from the whole body of source material, not a subset.
3. As an Admin, I want every passage to carry a Category, so that answers and future evaluations can be sliced by subfield.
4. As an Admin, I want to see how many documents and passages exist per register after ingestion, so that I can confirm the whole Corpus loaded.
5. As a User, I want a grounded Answer to always carry a Category and at least one Citation, so that "grounded" is a promise, not a hope.
6. As a User, I want an Insufficient-Context Answer to never carry text or Citations, so that a decline is unambiguous.
7. As a developer, I want the `Answer` contract to reject an ill-formed instance at construction, so that a bug that mislabels state fails loudly instead of shipping a bad payload.
8. As a developer, I want ingestion to skip an unreadable or empty source without aborting the whole run, so that one bad file doesn't block the Corpus.
9. As a developer, I want re-ingesting the whole Corpus to stay idempotent and orphan-free, so that a re-run reflects exactly the current sources.
10. As an operator, I want corpus statistics available from the CLI, so that I can verify state without opening the database.

## Implementation Decisions

- **`corpus` reader gains a JSON handler** alongside markdown/PDF. It reads the PLOS article JSON
  (title, abstract/body, article-level locators) into the same `Document` shape; the reader is chosen
  by file extension. One document per article.
- **Category assignment.** Priority: markdown front matter → a per-source manifest entry → a default
  Category for the register. The default keeps every passage Categorized without hand-labeling the
  whole Corpus; front matter/manifest override where known.
- **`Answer` contract invariants** move into the Pydantic model as validators:
  `grounded` ⇒ `text` non-empty, `category` set, `citations` non-empty; `insufficient_context` ⇒
  `text is None`, `category is None`, `citations == []`. Construction of a violating `Answer` raises.
- **Corpus statistics** are computed from the passages table (no new table): documents = distinct
  `source_ref`, passages grouped by `register`. Exposed as a `corpus stats` CLI subcommand and a
  read function in `core/store`. No documents table is introduced (YAGNI — the denormalized
  passage columns already carry document identity).
- **Ingestion robustness.** A source that fails to parse or yields no text is skipped with a warning;
  the run continues and reports how many were skipped. Whole-Corpus ingestion remains idempotent and
  orphan-free (M1's `replace_passages`, extended to the full set of loaded documents).
- **Threshold default.** The live run showed `grounding_threshold = 0.35` is too permissive for
  bge-small; the default moves to a value that separates on-topic from off-topic for that model
  (~0.5). Final calibration is M7's evals; this is a better starting default.

## Testing Decisions

- **Seams unchanged from M1:** ingestion + stats through the **CLI seam**, the `Answer` contract at
  the **type seam** (construct and assert it raises / accepts), retrieval/chat through the **HTTP and
  service seams**, all over a **real ephemeral pgvector** with the **FakeGateway** as the one stub.
- **Prior art:** M1's `tests/test_corpus_ingest.py` (CLI-seam ingestion) and `tests/test_chat.py`.
- **New coverage:** JSON fixture ingests into passages with correct register/Category; whole-fixture
  ingestion across all three registers reports expected counts; `corpus stats` returns per-register
  document/passage counts; an unreadable/empty fixture is skipped without aborting; the `Answer`
  model raises on each ill-formed combination and accepts the two valid shapes.
- Tests never assert semantic relevance (that's M7 evals); they assert structure, counts, and contract.

## Out of Scope

- The agent graph, tool-calling, multi-turn, checkpointer (M3); safety nodes (M4); the model gateway
  registry (M5); auth/RBAC — including *admin-gated* access to corpus-stats (M6); evals + threshold
  calibration (M7); frontend (M8); deploy (M9).
- Reranking, Redis semantic cache (documented future upgrades).
- A separate documents table (not needed; revisit only if document-level metadata grows).

## Further Notes

- Real embeddings still come from local sentence-transformers (`embeddings` extra) and synthesis from
  LiteLLM (`synthesis` extra, needs a key); tests use FakeGateway. Whole-Corpus ingestion with real
  embeddings is a heavier run (the OpenStax textbook alone is 55 MB / thousands of chunks) — batched
  embedding already handles it, but expect minutes, not seconds, for a real full ingest.
- corpus-stats here is unauthenticated; M6 puts it behind the Admin role.
