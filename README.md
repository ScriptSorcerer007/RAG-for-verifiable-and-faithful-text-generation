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

📄 Detailed Documentation:  
👉 [Phase 2 Documentation](./PHASE_2_QUERY_INTELLIGENCE.md)

---

---

### ✅ Phase 3 — Adaptive Retrieval
- Dynamic weighting of FAISS (semantic) and BM25 (keyword) retrieval
- Query-aware retrieval strategies (factual, conceptual, analytical, keyword)
- Adaptive hybrid scoring (α × dense + β × BM25)
- Noise filtering for improved result quality
- Improved precision and contextual relevance

📄 Detailed Documentation:  
👉 [Phase 3 Documentation](./PHASE_3_ADAPTIVE_RETRIEVAL.md)

---

### ✅ Phase 5 — Contextual Memory Lite
- Session-based short-term conversational memory
- Remembers recent messages
- Follow-up question understanding
- Prompt memory injection for context-aware answers
- Automatic memory trimming for efficiency
- Clear memory endpoint for fresh conversations

📄 Detailed Documentation:  
👉 [Phase 5 Documentation](./PHASE_5_CONTEXTUAL_MEMORY.md)


### ✅ Phase 6 — Performance Optimization
- Global model loading for faster requests
- Answer + embedding caching system
- Smart query expansion for short queries
- Query deduplication for cleaner retrieval
- Optimized reranking with limited candidates
- Junk chunk filtering before reranking
- Gemini API timeout + smart verification mode
- Same PDF upload reuse (skip reindexing)
- Runtime response time monitoring
- Faster overall system performance

📄 Detailed Documentation:  
👉 [Phase 6 Documentation](./PHASE_6_PERFORMANCE_OPTIMIZATION.md)

### ✅ Phase 7 — Security & Robustness
- Prompt injection protection (blocks malicious instructions)
- Input validation & sanitization (prevents XSS/injection attacks)
- Session-based rate limiting (prevents abuse & spam)
- Secure file upload handling (type & size validation)
- Middleware-based request filtering (blocks suspicious agents)
- Safe error handling (no internal traceback leaks)
- Logging system for monitoring and debugging
- Environment-based secrets management (.env)
- Production-ready security settings (cookies, headers,)

📄 Detailed Documentation:  
👉 [Phase 7 Documentation](./PHASE_7_SECURITY_AND_ROBUSTNESS.md)

## 🔄 Phase 4 — Chat History (Upcoming)
- Store user queries and responses
- Persistent chat history per user
- Context-aware conversation handling