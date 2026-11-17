# RedThread AI Evaluation & Benchmark Framework

## 1. Evaluation Philosophy

An AI application in the investigative domain cannot be validated merely by checking for HTTP 200 responses. Hallucinations, missed connections, or misattributed citations have catastrophic real-world consequences.

RedThread employs a rigorous, multi-dimensional evaluation harness comparing:
1. **Vector-Only Retrieval** (baseline chunk embeddings).
2. **Graph-Only Retrieval** (unweighted topological traversal).
3. **RedThread Hybrid Retrieval** (Graph traversal + vector context + grounded LLM synthesis).

---

## 2. Benchmark Dataset Architecture

The benchmark suite consists of **200–500 curated, synthetic investigative cases** paired with ground-truth question-answer-evidence triples across seven distinct investigative categories:

| Category | Description | Ground Truth Requirement |
| :--- | :--- | :--- |
| **Single-Hop** | Direct facts stated within a single document (*"Who is the beneficial owner of Shell Corp Y?"*). | Must identify document ID, page, and exact claim ID. |
| **Multi-Hop** | Relationships spanning 2 to 5 distinct documents (*"How is Person A connected to Account Z?"*). | Must return the complete unbroken sequence of intermediate entities and document citations. |
| **Cross-Case** | Overlapping entities shared across isolated case files (*"Which entities appear in both Case 101 and Case 204?"*). | Identifies shared canonical entities while respecting case permissions. |
| **Entity Resolution** | Queries with name variations, aliases, and corporate abbreviations (*"Did T.C.S. receive funds from Global Trade?"*). | Verifies that aliases resolve to the same canonical entity without false positives. |
| **Contradiction** | Cases containing conflicting reports (e.g., initial charge vs. exonerating audit). | Must report the dispute, present both claims, and refrain from drawing a false conclusion. |
| **Unanswerable** | Inquiries where evidence is incomplete or completely absent. | System must explicitly return an *Insufficient Evidence* warning rather than hallucinating. |
| **Citation Accuracy**| Testing whether cited pages and offsets genuinely contain the stated claim. | Verified against character offset boundaries in the source document. |

---

## 3. Evaluation Metrics

### 3.1 Retrieval Quality Metrics

$$\text{Precision}@K = \frac{|\text{Relevant Retrieved Items} \cap \text{Top } K|}{K}$$

$$\text{Recall}@K = \frac{|\text{Relevant Retrieved Items} \cap \text{Top } K|}{|\text{All Relevant Items}|}$$

$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

$$\text{nDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$

### 3.2 Generation & Groundedness Metrics (LLM-as-a-Judge + Ragas)

| Metric | Target SLA | Method |
| :--- | :---: | :--- |
| **Faithfulness** | $\ge 98\%$ | Evaluates whether every factual assertion in the generated answer is directly entailed by the retrieved evidence chunks. |
| **Answer Relevance** | $\ge 95\%$ | Evaluates whether the generated response directly addresses the investigator's question. |
| **Citation Correctness**| $100\%$ | Automated check verifying that cited Claim IDs exist and cited text offsets match source files. |
| **Unsupported Claim Rate**| $0.0\%$ | Flags any sentence containing an entity relationship not substantiated by an active claim citation. |

---

## 4. Benchmark Execution Script

Automated evaluations are executed via the CLI:
```bash
python -m backend.app.evaluation.benchmark \
    --dataset backend/app/evaluation/datasets/investigative_bench_v1.json \
    --modes vector,graph,hybrid \
    --output docs/benchmarks/results/latest_run.json
```

### Initial Baseline Results (15 Curated Test Cases)
| Query Type | Vector Baseline | Graph Only | RedThread Hybrid |
| :--- | :---: | :---: | :---: |
| Single-hop (N=7) | 85% (6/7) | 100% (7/7) | **100% (7/7)** |
| Multi-hop (N=8) | 25% (2/8) | 75% (6/8) | **100% (8/8)** |
| Total Accuracy | 53% (8/15) | 86% (13/15) | **100% (15/15)** |
