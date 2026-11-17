# ADR-003: Hybrid Graph-Vector Retrieval for Multi-Hop Inquiries

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
Standard Retrieval-Augmented Generation (RAG) relies almost entirely on dense vector embedding similarity (e.g. cosine distance over chunk embeddings).

In investigative intelligence, however, questions frequently demand tracing relational linkages across completely disparate documents:
> *"How is Person A connected to Organization Z?"*

In a multi-hop scenario:
- Doc 1: Person A $\rightarrow$ Company X
- Doc 2: Company X $\rightarrow$ Account Y
- Doc 3: Account Y $\rightarrow$ Person B
- Doc 4: Person B $\rightarrow$ Organization Z

The semantic cosine similarity between Person A's wire transfer and Organization Z's corporate charter is near zero. Vector search alone retrieves irrelevant passages or misses intermediate steps, resulting in hallucinated or inconclusive answers. Conversely, graph-only retrieval lacks rich semantic nuance and natural-language comprehension of complex queries.

## Decision
We implement a **13-Stage Hybrid Retrieval Strategy**:
1. **Query Parsing**: Extract seed entities and intent using Gemini classification.
2. **Graph Traversal (Path Discovery)**: Traversal engine queries Cognee using BFS to discover relationship chains up to $N \le 4$ hops connecting seed entities.
3. **Vector Passage Retrieval**: Queries vector index for passages semantically relevant to the question to retrieve qualitative context.
4. **Evidence Convergence & Ranking**: Retrieved graph paths and vector passages are merged, verified against case authorization, and filtered by claim status.
5. **Grounded Generation**: Gemini synthesizes the answer, strictly bound to verified claims and providing explicit citations for every hop.
6. **Fallback**: Returns `"Insufficient evidence"` if no path or verified evidence exists.

## Consequences
- **Positive**: Solves multi-hop cross-document reasoning that vector search fails; produces deterministic, audit-traceable path evidence.
- **Negative**: Retrieval latency is slightly higher than pure vector search (typically 600–1200ms vs 200ms); requires both graph and vector indexes to be synchronized.

---

## Related Documents
- [Hybrid Recall & RAG](../hybrid-recall-and-rag.md)
- [Evaluation Framework](../benchmarks/evaluation-framework.md)
