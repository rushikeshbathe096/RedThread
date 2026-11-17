# Module 7: Intelligent Recall & Grounded RAG

> **Document Status**: `DESIGN`  
> **Module ID**: `MOD-07`  
> **Responsibility**: 13-stage hybrid recall pipeline, multi-hop question answering, strict citation verification, and hallucination prevention.

---

## 1. Purpose & Scope
Intelligent Recall is RedThread's conversational AI assistant. It allows investigators to query the evidence base using natural language:
> *"How is John Smith connected to Person B, and what are the sources?"*

The system discovers multi-hop graph paths, pairs them with semantically relevant document chunks, verifies access permissions, and synthesizes an answer with exact citations.

---

## 2. Hybrid Retrieval Architecture

```mermaid
flowchart TD
    UserQuery[Investigator Query] --> Intent[Query & Entity Parsing]
    Intent --> GraphEngine[Graph Traversal: BFS / Dijkstra]
    Intent --> VectorEngine[Vector Passage Similarity]
    
    GraphEngine --> EvidenceRanker[Evidence Verification & Ranker]
    VectorEngine --> EvidenceRanker
    
    EvidenceRanker --> AuthFilter[Filter Unauthorized & Retracted Claims]
    AuthFilter --> PromptSynth[Grounded Synthesis Prompt]
    PromptSynth --> Gemini[Google Gemini 1.5 Pro]
    Gemini --> FinalAnswer[Answer + Source Citations + Path Graph]
```

---

## 3. Strict AI Safeguards
- **Zero Extrapolation**: If evidence is missing, the assistant outputs `"Insufficient evidence to establish connection"`.
- **Mandatory Dispute Citations**: Any claim marked `DISPUTED` in the retrieved path is explicitly highlighted with counter-evidence.
- **Traceable Path Output**: The returned `path` array is populated strictly from retrieved graph edges, not hallucinated text strings.

---

## 4. Related Documents
- [Hybrid Recall & RAG](../hybrid-recall-and-rag.md)
- [ADR-003: Hybrid Graph-Vector Recall](../decisions/ADR-003-hybrid-graph-vector-recall.md)
- [Evaluation Framework](../benchmarks/evaluation-framework.md)
