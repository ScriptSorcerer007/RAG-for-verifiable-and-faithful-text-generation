# 📘 Phase 5 — Contextual Memory Lite & Conversational RAG

---

# 🔷 Objective

Upgrade the RAG system from a single-turn question-answer engine into a **multi-turn conversational assistant** by introducing lightweight contextual memory.

The system now remembers recent messages, understands follow-up questions, and uses previous conversation context while generating answers.

---

# 🧠 Problem Before Phase 5

In earlier phases, the system processed each query independently:

```text
User Query
 → Retrieval
 → Reranking
 → Answer


1. Memory Size Control

Only the most recent messages are stored:

MAX_MEMORY = 6

Meaning:
Last 6 total messages retained
Prevents oversized prompts
Keeps response fast and efficient

2. Prompt Injection

The LLM prompt now includes previous context:

Previous Conversation:
{memory_text}

Evidence:
{context}

Question:
{query}

This enables contextual understanding.

👉 Example:

Q1: What is RAG?
Q2: Why is it important?

👉 System understands:
“it = RAG”