# 📘 Phase 1 — RAG System Implementation

## 🔷 Objective

Build a Retrieval-Augmented Generation (RAG) system that:

* Processes PDF documents
* Retrieves relevant information
* Generates grounded answers with sources

---

# 🧠 System Pipeline

```text
User Query
   ↓
Hybrid Retrieval (FAISS + BM25)
   ↓
Score Fusion
   ↓
Cross-Encoder Reranking
   ↓
Context Building
   ↓
LLM (Gemini) Answer Generation
   ↓
Verification + Confidence Score
```

---

# ⚙️ What Was Implemented

## 1. 📄 PDF Processing

* Extracted text using `PyMuPDF (fitz)`
* Split into chunks:

  * chunk_size = 1000
  * overlap = 200

---

## 2. 🔍 Dense Retrieval (FAISS)
[text](PHASE_1_RAG_DOCUMENTATION.md)
* Used embeddings model:

  * `all-MiniLM-L6-v2`
* Stored vectors in FAISS

👉 Purpose: semantic search

---

## 3. 🔎 Sparse Retrieval (BM25)

* Implemented custom BM25 retriever
* Tokenized using `.split()`

👉 Purpose: keyword matching

---

## 4. 🔗 Hybrid Retrieval

* Combined FAISS + BM25
* Used score normalization
* Merged results with weighted scoring

👉 Output:

```python
[(document, hybrid_score)]
```

---

## 5. 🎯 Reranking (Cross-Encoder)

* Model: `ms-marco-MiniLM-L-6-v2`
* Ranked documents using query-document pairs

👉 Output:

```python
[(document, reranker_score)]
```

---

## 6. 📊 Score Processing

### Applied:

* Sigmoid normalization (stability)
* Min-Max normalization (ranking strength)

### Final score:

```python
final_score = 0.5 * sigmoid + 0.5 * minmax
```

---

## 7. 🧾 Context Construction

* Selected top 5 documents
* Structured as:

```text
[1] content
[2] content
...
```

---

## 8. 🤖 Answer Generation

* Used Gemini API
* Prompt includes:

  * Evidence
  * Question
  * Citation instructions

---

## 9. 📏 Alignment Score

* Measured similarity between:

  * Answer
  * Retrieved context

---

## 10. ✅ Verification

* Used LLM to check:

  * Faithfulness score
  * Hallucination
  * Explanation

---

## 11. 📈 Confidence Score

Combined multiple signals:

```python
confidence =
    0.3 * retrieval_score +
    0.2 * hybrid_score +
    0.3 * alignment_score +
    0.2 * faithfulness
```

---

## 12. 🔗 Source Attribution

* Returned:

  * Rank
  * Score
  * Page number
  * Document link

---

# 🧪 Key Improvements Made

* Implemented hybrid retrieval (BM25 + FAISS)
* Added reranking layer
* Introduced score normalization
* Fixed JSON serialization issues
* Built multi-factor confidence system

---

# 🎯 Outcome

* Accurate answers grounded in documents
* Relevant sources with citations
* Stable and meaningful confidence scores

---

# 🏁 Status

✅ Phase 1 Complete
→ System works as a **retrieval-based QA engine**
