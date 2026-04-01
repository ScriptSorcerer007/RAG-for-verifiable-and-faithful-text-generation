# VeritasAI — Retrieval-Augmented Generation for Verifiable and Faithful Text Generation

VeritasAI is an advanced **Retrieval-Augmented Generation (RAG) system** designed to generate **factually grounded and verifiable answers** from documents.  
Unlike standard generative models that hallucinate information, this system retrieves evidence from uploaded documents and verifies the generated answer against that evidence.

The system integrates **dense retrieval, sparse retrieval, hybrid search, reranking, and verification mechanisms** to improve factual accuracy and transparency.

---

# Project Domain

- Natural Language Processing (NLP)
- Generative AI
- Information Retrieval
- Explainable AI

---

# Problem Statement

Large Language Models often suffer from:

- Hallucinated facts
- Lack of evidence grounding
- Poor citation alignment
- Inconsistent factual outputs

This project aims to address these issues by building a **verifiable RAG pipeline**.

---

# Proposed Solution

The system introduces a **multi-stage RAG architecture**:


---

# 📌 Project Progress

### ✅ Phase 1 — Retrieval + Reranking Completed

Implemented:
- Hybrid Retrieval (FAISS + BM25)
- Score Normalization & Fusion
- Cross-Encoder Reranking
- Context-aware Answer Generation
- Verification & Confidence Scoring

📄 Detailed Documentation:  
👉 [Phase 1 Documentation](./PHASE_1_RAG_DOCUMENTATION.md)

---

### ✅ Phase 2 — Query Intelligence
- Query Classification (factual, conceptual, analytical, keyword)
- Multi-Query Expansion using LLM
- Multi-Query Retrieval Pipeline
- Deduplication with score optimization
- Result sorting and controlled reranking

📄 Details: [Phase 2 Documentation](./PHASE_2_QUERY_INTELLIGENCE.md)

---