# Single Postgres (pgvector) for both relational and vector data

We store application data (users, conversations, messages, documents) **and** vector embeddings
in one Postgres instance using the `pgvector` extension, instead of running a dedicated vector
database (Pinecone, Weaviate, Qdrant) alongside a relational DB.

## Why

- The corpus is bounded (tens of documents, not millions of vectors); pgvector with an HNSW index
  is more than fast enough at this scale.
- One database means one connection, one backup story, one transaction boundary, and no
  cross-store consistency problems between a chunk's metadata and its embedding.
- Fewer moving parts for a solo, MVP-first build — and a cleaner "one `docker compose up`" story.

## Trade-off / consequences

- At very large scale (millions of vectors, high QPS) a dedicated vector DB would outperform this.
  Migrating later means moving embeddings out and adapting the retrieval layer — non-trivial, hence
  this is recorded.
- The embedding **dimension is fixed at index-build time** (currently 384 for `bge-small-en-v1.5`);
  changing the embedding model requires re-embedding the whole corpus.
