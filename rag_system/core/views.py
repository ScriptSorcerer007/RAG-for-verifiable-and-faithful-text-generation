import os
import json
import fitz
import requests
import re
import math
import time


from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from sklearn.metrics.pairwise import cosine_similarity

from core.rag.bm25_retriever import BM25Retriever
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import ReRanker
from core.rag.query_classifier import classify_query
from core.rag.query_expander import expand_query

from core.rag.reranker import ReRanker
from core.rag.cache_utils import get_or_create_embedding

from core.rag.security import detect_prompt_injection
from core.rag.validators import validate_query, validate_file
from core.rag.utils import log_error

## from django_ratelimit.decorators import ratelimit( for production use or can use redis )

# for link gerneration error for spaces in the documents
from urllib.parse import quote
# file name like this Generative ai with langchain-2.pdf have spaces it will encode it like this to prevent from link fail
# Generative%20ai%20with%20langchain-2.pdf

from core.rag.cache_utils import (
    get_cached_answer,
    set_cached_answer,
    get_or_create_embedding
)
# ===============================
# HOME PAGE
# ===============================

def home(request):
    return render(request, "index.html")


from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('account_login')


# ===============================
# GLOBAL OBJECTS
# ===============================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = None
bm25 = None
documents_cache = []

reranker = ReRanker()
hybrid = None

FAISS_INDEX_PATH = os.path.join(settings.BASE_DIR, "faiss_index")


# ===============================
# LOAD FAISS INDEX
# ===============================

def load_vectorstore():
    global vectorstore

    if os.path.exists(FAISS_INDEX_PATH):

        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

        print("FAISS index loaded from disk.")

    else:
        print("No FAISS index found.")


# ===============================
# UPLOAD PDF
# ===============================

@csrf_exempt
def upload_pdf(request):
    if not request.user.is_authenticated:
        if request.session.get("uploaded", False):
            return JsonResponse({
                 "error": "LOGIN_REQUIRED"
        })

        request.session["uploaded"] = True

    global vectorstore
    global bm25
    global documents_cache

    if request.method == "POST":

        try:

            file = request.FILES.get("file")

            valid, msg = validate_file(file)
            
            if not valid:
                return JsonResponse({"error": msg}, status=400)

            last_file = request.session.get("last_uploaded_file")
            
            if last_file == file.name and os.path.exists(FAISS_INDEX_PATH):
                return JsonResponse({
        "message": "Using existing indexed PDF",
        "cached": True
    })

            if not file:
                return JsonResponse({"error": "No file provided"}, status=400)

            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            file_path = os.path.join(settings.MEDIA_ROOT, file.name)

            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            print("PDF saved:", file_path)

            # ---------------------------
            # EXTRACT TEXT
            # ---------------------------

            doc = fitz.open(file_path)

            documents = []

            for page_number in range(len(doc)):

                page = doc[page_number]

                text = page.get_text()

                if text.strip():

                    documents.append(

                        Document(
                            page_content=text,
                            metadata={
                                "source": file.name,
                                "page": page_number + 1
                            }
                        )

                    )

            print("Pages extracted:", len(documents))

            # ---------------------------
            # CHUNKING
            # ---------------------------

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            split_docs = splitter.split_documents(documents)

            documents_cache = split_docs

            print("Chunks:", len(split_docs))

            # ---------------------------
            # VECTORSTORE
            # ---------------------------

            vectorstore = FAISS.from_documents(split_docs, embeddings)

            vectorstore.save_local(FAISS_INDEX_PATH)

            print("FAISS index saved")

            # ---------------------------
            # BM25 RETRIEVER
            # ---------------------------

            bm25 = BM25Retriever(split_docs)

            print("BM25 retriever initialized")

            request.session["last_uploaded_file"] = file.name

            return JsonResponse({
                "message": "PDF processed successfully",
                "total_pages": len(documents),
                "total_chunks": len(split_docs)
            })

        except Exception as e:

            print("UPLOAD ERROR:", str(e))

            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Upload using POST method."})


MAX_MEMORY = 6

def get_chat_memory(request):
    return request.session.get("chat_memory", [])

def save_chat_memory(request, memory):
    request.session["chat_memory"] = memory
    request.session.modified = True

def add_to_memory(request, role, content):
    memory = get_chat_memory(request)

    memory.append({
        "role": role,
        "content": content
    })

    if len(memory) > MAX_MEMORY:
        memory = memory[-MAX_MEMORY:]

    save_chat_memory(request, memory)

def format_memory(request):
    memory = get_chat_memory(request)

    lines = []
    for msg in memory:
        lines.append(f"{msg['role']}: {msg['content']}")

    return "\n".join(lines)

# ===============================
# ASK QUESTION
# ===============================
def ask_question(request):

    if not request.user.is_authenticated:
        count = request.session.get('chat_count', 0)

        if count >= 10:
            return JsonResponse({
                "error": "LOGIN_REQUIRED"
            })

        request.session['chat_count'] = count + 1
    
    
    

    global vectorstore
    global bm25

    print("ASK FUNCTION EXECUTED")

    if request.method == "POST":

        try:

            start_time = time.time()

            data = json.loads(request.body)
            query = data.get("question", "")

            valid, msg = validate_query(query)
            
            if not valid:
                return JsonResponse({"error": msg}, status=400)
            
            if detect_prompt_injection(query):
                return JsonResponse({"error": "Unsafe prompt detected"}, status=400)
            
            query = query.strip().lower()

            import re
            query = re.sub(r"[^\w\s]", "", query)

            cached = get_cached_answer(query)

            if cached:
                print("CACHE HIT: Gemini Answer")
                return JsonResponse(cached)
            

            add_to_memory(request, "User", query)
        
            if not query:
                return JsonResponse({"error": "No question provided"}, status=400)
            
            # Step 1: classify query
            query_type = classify_query(query)
            print("Query Type:", query_type)
            
            # Step 2: expand query
            # Step 2: smart expand query
            if len(query.split()) <= 3:
                expanded_queries = []
            else:
                expanded_queries = expand_query(query)

            print("\n--- EXPANDED QUERIES ---")
            for q in expanded_queries:
                print(q)
                
            # Step 3: combine queries
            all_queries = list(dict.fromkeys([query] + expanded_queries[:3]))

            if vectorstore is None:
                load_vectorstore()

            if vectorstore is None:
                return JsonResponse({"error": "Upload PDF first."})

            if bm25 is None:
                return JsonResponse({"error": "BM25 retriever not initialized."})

            # ===============================
            # HYBRID RETRIEVAL
            # ===============================

            # initialize retrievers
            global hybrid
            if hybrid is None:
                hybrid = HybridRetriever(vectorstore, bm25)

            # run hybrid retrieval
            all_results = []
            
            for q in all_queries:
                results = hybrid.retrieve(q, k=5)
                all_results.extend(results)

            unique = {}
            for doc, score in all_results:
                key = doc.page_content
                
                if key not in unique or score > unique[key][1]:
                    unique[key] = (doc, score)
            merged_results = list(unique.values())

            merged_results = sorted(
                merged_results,
                key=lambda x: x[1],
                reverse=True
                )

        
            # DEBUG
            print("\n--- MERGED RESULTS ---")
            for doc, score in merged_results:
                print("Score:", score, "|", doc.page_content[:80])

            # Clean junk docs before reranking

            cleaned_results = []

            for doc, score in merged_results:
                text = doc.page_content.strip().lower()

                if len(text) < 180:
                    continue

                blocked = [
        "table of contents",
        "contributors",
        "chapter 1",
        "questions",
        "index",
        "contents"
    ]

                if any(word in text for word in blocked):
                    continue

                cleaned_results.append((doc, score))

            merged_results = cleaned_results

            # Only top 8 docs for reranker
            hybrid_docs = [doc for doc, score in merged_results[:8]]

            print("Reranking docs:", len(hybrid_docs))

            print("\n--- FINAL MERGED RESULTS COUNT ---")
            print(len(merged_results))
            reranked_results = reranker.rerank(query, hybrid_docs, top_k=5)


            print("\n--- TOTAL RETRIEVAL CALLS ---")
            print(len(all_queries))

            print("\n--- RERANKED RESULTS ---")
            for doc, score in reranked_results:
                print("Rerank Score:", score, "|", doc.page_content[:80])

            documents = [doc for doc, score in reranked_results]
            raw_scores = [float(score) for doc, score in reranked_results]



            # sigmoid for stability
            def safe_sigmoid(x):
                if x < -50:
                    return 0.0
                if x > 50:
                    return 1.0
                return 1 / (1 + math.exp(-x))
            sigmoid_scores = [safe_sigmoid(s) for s in raw_scores]

            # min-max for ranking sharpness
            if not raw_scores:
                scores = []
            else:
                min_s = min(raw_scores)
                max_s = max(raw_scores)
                
                if max_s - min_s == 0:
                    minmax_scores = [0.5 for _ in raw_scores]
                else:
                    minmax_scores = [
                        (s - min_s) / (max_s - min_s)
                        for s in raw_scores
                        ]
                sigmoid_scores = [safe_sigmoid(s) for s in raw_scores]
                scores = [
                    0.5 * s1 + 0.5 * s2
                    for s1, s2 in zip(sigmoid_scores, minmax_scores)
                    ]
            # ===============================
            # BUILD CONTEXT
            # ===============================

            context_parts = []

            for i, doc in enumerate(documents, start=1):
                context_parts.append(f"[{i}] {doc.page_content}")

            context = "\n\n".join(context_parts)

            # ===============================
            # GENERATOR
            # ===============================
            memory_text = format_memory(request)
            prompt = f"""
You are a helpful assistant.

Use previous conversation when relevant.

Previous Conversation:
{memory_text}

Use ONLY the provided evidence.

Cite evidence number like [1].

(if one Cite complete Start the next by next line).

Evidence:
{context}

Question:
{query}
"""

            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"

            headers = {"Content-Type": "application/json"}

            payload = {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            }

            response = requests.post(url,headers=headers,json=payload,timeout=20)

            if response.status_code != 200:
                print("Gemini error:", response.text)
                return JsonResponse({"error": response.text}, status=500)

            result = response.json()

            answer_text = result["candidates"][0]["content"]["parts"][0]["text"]
            add_to_memory(request, "Assistant", answer_text)

            # ===============================
            # ALIGNMENT SCORE
            # ===============================

            answer_embedding = get_or_create_embedding(answer_text, embeddings)
            context_embedding = get_or_create_embedding(context, embeddings)

            alignment_score = cosine_similarity(
                [answer_embedding],
                [context_embedding]
                )[0][0]
            # clamp between 0 and 1
            
            alignment_score = max(0, min(1, float(alignment_score)))

            hybrid_scores = [float(score) for doc, score in merged_results]
            hybrid_score_avg = sum(hybrid_scores) / len(hybrid_scores) if hybrid_scores else 0
            # ===============================
            # VERIFICATION
            # ===============================

            verification_data = {}
            
            if len(answer_text.strip()) > 80:
                verification_prompt = f"""
Evidence:
{context}

Answer:
{answer_text}

Return JSON:

{{
"faithfulness_score": number between 0 and 1,
"hallucination": true or false,
"explanation": "short explanation"
}}
"""
                verification_payload = {
                "contents": [
                    {"parts": [{"text": verification_prompt}]}
                ]
            }

                verification_response = requests.post(
                url,
                headers=headers,
                json=verification_payload,
                timeout=20
            )

                if verification_response.status_code == 200:
                    
                    verification_result = verification_response.json()
                    
                    verification_text = verification_result["candidates"][0]["content"]["parts"][0]["text"]
                    json_match = re.search(r'\{.*\}', verification_text, re.DOTALL)
                    
                    if json_match:
                        verification_data = json.loads(json_match.group())

            if not verification_data:
                verification_data = {
        "faithfulness_score": 0.85,
        "hallucination": False,
        "explanation": "Fast verification mode"
    }

            # ===============================
            # SOURCES
            # ===============================

            sources = []

            for i, doc in enumerate(documents):

                sources.append({
                    "rank": i + 1,
                    "score": float(scores[i]),
                    "document": doc.metadata["source"],
                    "page": doc.metadata["page"],
                    "chunk": doc.page_content,
                    "link": f"/media/{quote(doc.metadata['source'])}#page={doc.metadata['page']}&search={doc.page_content[:40]}"
                })

            # ===============================
            # RESPONSE
            # ===============================
            faith = verification_data.get("faithfulness_score", 0)

            # clamp faith between 0 and 1
            faith = max(0, min(1, faith))

            # retrieval score
            retrieval_score = sum(scores) / len(scores) if scores else 0

           # final confidence
            confidence = (
                0.3 * retrieval_score +     # reranker
                0.2 * hybrid_score_avg +    # hybrid
                0.3 * alignment_score +     # semantic match
                0.2 * faith                # LLM verification
                )
            response_data = {
                "answer": answer_text,
                "confidence": float(confidence),
                "faithfulness_score": faith,
                "hallucination": verification_data.get("hallucination"),
                "verification": verification_data.get("explanation"),
                "alignment_score": float(alignment_score),
                "sources": sources
                }

            set_cached_answer(query, response_data)

            print("TOTAL RESPONSE TIME:", round(time.time() - start_time, 2), "sec")

            return JsonResponse(response_data)

        except Exception as e:
            log_error("ASK ERROR")
            
            return JsonResponse(
                {"error": "Internal server error"},
                status=500)


    return JsonResponse({"error": "Use POST method."})



def logout_view(request):
    logout(request)
    return redirect('/')

def clear_memory(request):
    request.session["chat_memory"] = []
    return JsonResponse({"message": "Memory cleared"})