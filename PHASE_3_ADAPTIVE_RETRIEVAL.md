# 📘 Phase 3 — Adaptive Retrieval & Query-Aware Search

---

# 🔷 Objective

Enhance the RAG system by introducing **adaptive retrieval strategies** that dynamically adjust search behavior based on query intent.

---

# 🧠 Problem in Phase 2

Although Phase 2 introduced query intelligence:

```text
Query → Classification → Expansion → Multi-Retrieval
```

The system still had a limitation:

* Same retrieval strategy for all queries
* Equal importance to semantic and keyword search
* Limited differentiation in results across query types

---

# 🚀 Solution — Adaptive Retrieval

Phase 3 introduces **query-aware retrieval weighting**:

```text
Query
 → Query Classification 🧠
 → Adaptive Weight Selection ⚖️
 → Hybrid Retrieval (FAISS + BM25)
 → Reranking
 → Answer
```

---

# ⚙️ Key Concept

## Hybrid Retrieval Formula

```text
Final Score = α × Dense Score + β × BM25 Score
```

Where:

* **Dense Score (FAISS)** → semantic similarity
* **BM25 Score** → keyword relevance
* **α (alpha)** → weight for dense retrieval
* **β (beta)** → weight for BM25 retrieval

---

# 🎯 Adaptive Strategy

The system dynamically adjusts weights based on query type:

| Query Type | Description  | α (Dense) | β (BM25) |
| ---------- | ------------ | --------- | -------- |
| Factual    | Definitions  | 0.5       | 0.5      |
| Conceptual | Explanations | 0.9       | 0.1      |
| Analytical | Reasoning    | 0.7       | 0.3      |
| Keyword    | Lists / Code | 0.1       | 0.9      |

---

# 🧠 Query Classification

The query is classified into one of four types:

```python
def classify_query(query):
    ...
```

This classification drives the retrieval strategy.

---

# 🔄 Adaptive Retrieval Flow

```text
User Query
   ↓
Query Classification
   ↓
Weight Selection (α, β)
   ↓
Multi-Query Expansion
   ↓
Hybrid Retrieval (Adaptive)
   ↓
Deduplication + Sorting
   ↓
Filtering (noise removal)
   ↓
Reranking
   ↓
Answer Generation
```

---

# 🔍 Implementation Details

---

## 1. Hybrid Retriever Update

The retriever was modified to support dynamic weights:

```python
def retrieve(self, query, k=10, alpha=0.5, beta=0.5):
```

---

## 2. Score Fusion

```python
score = alpha * dense_score + beta * bm25_score
```

---

## 3. Dynamic Weight Assignment

In `views.py`:

```python
if query_type == "conceptual":
    alpha, beta = 0.9, 0.1
```

---

## 4. Multi-Query Adaptive Retrieval

```python
for q in all_queries:
    results = hybrid.retrieve(q, k=5, alpha=alpha, beta=beta)
```

---

## 5. Noise Filtering

Low-quality chunks are removed:

```python
if len(doc.page_content.strip()) > 200
```

---

# 📈 Improvements Achieved

| Feature            | Phase 2     | Phase 3       |
| ------------------ | ----------- | ------------- |
| Retrieval strategy | Static      | Adaptive      |
| Query handling     | Intelligent | Context-aware |
| Precision          | Good        | 🔥 Higher     |
| Result diversity   | Medium      | 🔥 Improved   |
| Noise              | Present     | Reduced       |

---

# 🧪 Validation

System was tested with multiple query types:

### Factual Query

```text
What is LangChain?
```

→ Balanced retrieval

---

### Conceptual Query

```text
Explain LangChain architecture
```

→ Semantic-heavy retrieval

---

### Keyword Query

```text
LangChain code examples
```

→ Keyword-heavy retrieval

---

## Observations

* Different queries resulted in different retrieval strategies
* Retrieval scores varied based on weights
* Improved relevance of top-ranked documents
* Reduced irrelevant chunks (e.g., table of contents)

---

# 🎯 Outcome

Phase 3 transforms the system into:

> **A query-aware adaptive retrieval engine that dynamically adjusts its search strategy**

---

# 🏁 Status

✅ Phase 3 Complete
→ System supports **adaptive hybrid retrieval**

---

# 🚀 Next Phase

Phase 4 will introduce:

* User-based chat history
* Persistent conversation storage
* Context-aware answering

---
