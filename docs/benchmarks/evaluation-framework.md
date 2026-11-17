# RedThread AI Evaluation & Benchmark Framework

> **Document Status**: `DESIGN`  
> **Benchmark Scope**: 200-question ground-truth evaluation suite comparing Vector-Only, Graph-Only, and Hybrid Graph-Vector Retrieval.

---

## 1. Evaluation Methodology

An AI system in the investigative domain cannot be validated by HTTP status codes alone. RedThread executes an automated, reproducible benchmark across **200 curated, synthetic investigative inquiries** evaluated across three distinct splits:
- **Development Set (60 questions)**: Used for hyperparameter tuning (ranking weights, hop bounds).
- **Validation Set (40 questions)**: Used for regression testing during development phases.
- **Held-Out Test Set (100 questions)**: Reserved strictly for final performance scoring.

---

## 2. 200-Question Category Distribution

| Category | Questions | Description | Ground Truth Criteria |
| :--- | :---: | :--- | :--- |
| **Single-Hop Retrieval** | 30 | Direct facts within a single document (*"Who is the director of Company X?"*). | Must identify document ID, page, and exact claim ID. |
| **Multi-Hop Reasoning** | 40 | Chains of 2–5 hops across documents (*"How is Person A connected to Account Z?"*). | Must return complete unbroken sequence of intermediate entities. |
| **Cross-Document Connections** | 30 | Linking separate documents mentioning shared transaction IDs or accounts. | Validates edge synthesis across disparate file uploads. |
| **Cross-Case Retrieval** | 20 | Identifying shared entities across isolated cases while respecting permissions. | Discovers authorized overlaps without leaking unauthorized context. |
| **Entity Resolution** | 20 | Queries involving corporate acronyms, misspellings, and inverted names. | Verifies correct alias resolution and zero false merges. |
| **Contradiction Detection** | 20 | Inquiries where initial reports disagree with subsequent forensic audits. | Must identify dispute, present both views, and refuse premature conclusions. |
| **Unanswerable Inquiries** | 20 | Questions with missing or incomplete evidence. | Model must output *"Insufficient evidence"* rather than hallucinating. |
| **Evidence Citation** | 20 | Precise page and character offset verification. | Verifies that cited excerpts match raw document bytes exactly. |
| **Total** | **200** | | |

---

## 3. Metrics Suite

### 3.1 Retrieval Metrics
- **Recall@5**: Proportion of relevant evidence claims retrieved in the top 5 results.
- **Precision@5**: Proportion of top 5 retrieved claims that are relevant.
- **Mean Reciprocal Rank (MRR)**: Reciprocal rank of the first relevant claim.
- **nDCG@10**: Normalized Discounted Cumulative Gain accounting for position-weighted relevance.

### 3.2 Answer Quality & Groundedness Metrics
- **Answer Accuracy**: Semantic correctness evaluated against ground-truth answers.
- **Faithfulness**: Percentage of claims in the generated response directly supported by retrieved sources (Target: $\ge 98\%$).
- **Answer Relevance**: Semantic alignment between the answer and investigator's prompt.
- **Unsupported Answer Rate**: Percentage of answers containing un-cited factual assertions (Target: $0.0\%$).

### 3.3 Evidence & Citation Metrics
- **Citation Precision**: Proportion of generated citations that accurately support their sentence.
- **Citation Recall**: Proportion of required source claims that are explicitly cited.
- **Citation Correctness**: 100% verification that cited Claim IDs exist and offsets match raw source text.

### 3.4 Entity Resolution & Contradiction Metrics
- **Entity Resolution**: Precision, Recall, F1, and False Merge Rate (Target: $< 1.0\%$).
- **Contradiction Detection**: Precision, Recall, and F1 in identifying disputed claims.

### 3.5 System Performance Metrics
- **p50 & p95 Latency**: Retrieval latency and end-to-end response generation time.
- **Ingestion Throughput**: Documents processed per minute per worker.
- **Reliability**: Job failure rate and retry recovery success rate.
- **Cost Efficiency**: Token and API cost per document and per query.

---

## 4. Benchmark Execution

```bash
python -m backend.app.evaluation.benchmark \
    --dataset backend/app/evaluation/datasets/investigative_bench_200.json \
    --modes vector,graph,hybrid \
    --split test \
    --output backend/tests/evaluation/reports/benchmark_report.json
```

---

## 5. Related Documents
- [Performance Targets](performance-targets.md)
- [Hybrid Recall & RAG](../hybrid-recall-and-rag.md)
- [Testing Strategy](../testing-strategy.md)
