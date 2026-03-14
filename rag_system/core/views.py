import os
import json
import fitz
import requests
import re

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from sklearn.metrics.pairwise import cosine_similarity

from core.rag.bm25_retriever import BM25Retriever
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import ReRanker


# ===============================
# HOME PAGE
# ===============================

def home(request):
    return render(request, "index.html")


# ===============================
# GLOBAL OBJECTS
# ===============================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = None
bm25 = None
documents_cache = []

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

    global vectorstore
    global bm25
    global documents_cache

    if request.method == "POST":

        try:

            file = request.FILES.get("file")

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

            return JsonResponse({
                "message": "PDF processed successfully",
                "total_pages": len(documents),
                "total_chunks": len(split_docs)
            })

        except Exception as e:

            print("UPLOAD ERROR:", str(e))

            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Upload using POST method."})


# ===============================
# ASK QUESTION
# ===============================

@csrf_exempt
def ask_question(request):

    global vectorstore
    global bm25

    print("ASK FUNCTION EXECUTED")

    if request.method == "POST":

        try:

            data = json.loads(request.body)
            query = data.get("question")

            if not query:
                return JsonResponse({"error": "No question provided"}, status=400)

            if vectorstore is None:
                load_vectorstore()

            if vectorstore is None:
                return JsonResponse({"error": "Upload PDF first."})

            if bm25 is None:
                return JsonResponse({"error": "BM25 retriever not initialized."})

            # ===============================
            # HYBRID RETRIEVAL
            # ===============================

            hybrid = HybridRetriever(vectorstore, bm25)
            hybrid_results = hybrid.retrieve(query, k=10)

            print("Hybrid results:", len(hybrid_results))

            # ===============================
            # RERANKING
            # ===============================

            reranker = ReRanker()

            reranked_docs = reranker.rerank(query, hybrid_results, top_k=5)

            documents = reranked_docs
            scores = [1.0] * len(documents)

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

            prompt = f"""
You are a helpful assistant.

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

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                print("Gemini error:", response.text)
                return JsonResponse({"error": response.text}, status=500)

            result = response.json()

            answer_text = result["candidates"][0]["content"]["parts"][0]["text"]

            # ===============================
            # ALIGNMENT SCORE
            # ===============================

            answer_embedding = embeddings.embed_query(answer_text)
            context_embedding = embeddings.embed_query(context)

            alignment_score = cosine_similarity(
                [answer_embedding],
                [context_embedding]
            )[0][0]

            # ===============================
            # VERIFICATION
            # ===============================

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
                json=verification_payload
            )

            verification_data = {}

            if verification_response.status_code == 200:

                verification_result = verification_response.json()

                verification_text = verification_result["candidates"][0]["content"]["parts"][0]["text"]

                json_match = re.search(r'\{.*\}', verification_text, re.DOTALL)

                if json_match:
                    verification_data = json.loads(json_match.group())

            # ===============================
            # SOURCES
            # ===============================

            sources = []

            for i, doc in enumerate(documents):

                sources.append({
                    "rank": i + 1,
                    "score": scores[i],
                    "document": doc.metadata["source"],
                    "page": doc.metadata["page"],
                    "chunk": doc.page_content,
                    "link": f"/media/{doc.metadata['source']}#page={doc.metadata['page']}"
                })

            # ===============================
            # RESPONSE
            # ===============================

            return JsonResponse({

                "answer": answer_text,
                "faithfulness_score": verification_data.get("faithfulness_score"),
                "hallucination": verification_data.get("hallucination"),
                "verification": verification_data.get("explanation"),
                "alignment_score": float(alignment_score),
                "retrieval_scores": scores,
                "average_retrieval_score": sum(scores) / len(scores),
                "sources": sources

            })

        except Exception as e:

            print("ASK ERROR:", str(e))

            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Use POST method."})