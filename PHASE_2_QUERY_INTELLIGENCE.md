# 📘 Phase 2 — Query Intelligence & Multi-Query Retrieval

## 🔷 Objective

Enhance the RAG system by introducing **query understanding and intelligent retrieval strategies** to improve answer quality and coverage.

---

# 🧠 Problem in Phase 1

Phase 1 used a **single query → single retrieval** approach:

```text
Query → Retrieve → Answer
```

### Limitations:

* Weak queries → poor results
* No understanding of query intent
* Limited document coverage
* Static retrieval behavior

---

# 🚀 Solution — Query Intelligence Layer

Phase 2 introduces:

```text
Query
 → Query Classification 🧠
 → Query Expansion 🔁
 → Multi-Query Retrieval 🔍
 → Deduplication + Ranking 🎯
 → Reranking
 → Answer
```

---

# ⚙️ Components Implemented

---

## 1. 🧠 Query Classification

### Purpose:

Identify the type of query to enable intelligent retrieval.

### Types:

* **Factual** → definitions (e.g., “What is RAG?”)
* **Conceptual** → explanations (e.g., “Explain RAG pipeline”)
* **Analytical** → reasoning (e.g., “Why is RAG important?”)
* **Keyword-based** → direct matches (e.g., “RAG components list”)

### Implementation:

```python
def classify_query(query):
    ...
```

---

## 2. 🔁 Query Expansion

### Purpose:

Convert a single query into multiple semantically rich queries.

### Example:

```text
Input:
"What is RAG?"

Expanded:
- Define RAG
- Explain retrieval augmented generation
- RAG meaning in AI
```

### Implementation:

* Uses Gemini API
* Generates 3 variations
* Cleans output text

---

## 3. 🔍 Multi-Query Retrieval

### Process:

```text
Original Query + Expanded Queries
 → Multiple Retrieval Calls
```

### Code Flow:

```python
for q in all_queries:
    results = hybrid.retrieve(q, k=5)
```

---

## 4. 🧹 Deduplication with Score Preservation

### Problem:

Multiple queries return duplicate chunks.

### Solution:

Keep **best score per document**:

```python
if key not in unique or score > unique[key][1]:
    unique[key] = (doc, score)
```

---

## 5. 📊 Result Merging & Sorting

### Steps:

* Merge all results
* Sort by score

```python
merged_results = sorted(merged_results, key=lambda x: x[1], reverse=True)
```

---

## 6. 🎯 Controlled Reranking Input

### Improvement:

Limit documents passed to reranker:

```python
hybrid_docs = merged_results[:20]
```

### Benefits:

* Faster processing
* Better precision
* Reduced noise

---

# 📈 Improvements Achieved

| Feature        | Phase 1      | Phase 2     |
| -------------- | ------------ | ----------- |
| Query handling | Static       | Intelligent |
| Retrieval      | Single query | Multi-query |
| Coverage       | Limited      | Wide        |
| Accuracy       | Good         | 🔥 Improved |
| Flexibility    | ❌           | ✅           |

---

# 🧪 Validation

### Verified via:

* Terminal logs:

  * Query type detection
  * Expanded queries
  * Increased retrieval count
* Improved relevance of top-ranked documents
* Better alignment between query and answer

---

# 🎯 Outcome

Phase 2 transforms the system into:

> **An intelligent retrieval engine capable of understanding and expanding user queries**

---

# 🏁 Status

✅ Phase 2 Complete
→ System supports **query-aware, multi-query retrieval**

---

# 🚀 Next Phase

Phase 3 will introduce:

* Adaptive Retrieval (dynamic BM25 vs FAISS weighting)
* Query-type-based retrieval strategies

---
