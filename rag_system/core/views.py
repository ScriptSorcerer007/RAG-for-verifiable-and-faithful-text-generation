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

# ===============================
# HOME PAGE (WEB UI)
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
FAISS_INDEX_PATH = os.path.join(settings.BASE_DIR, "faiss_index")


# ===============================
# LOAD FAISS IF EXISTS
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
# UPLOAD PDF + BUILD INDEX
# ===============================

@csrf_exempt
def upload_pdf(request):
    global vectorstore

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

            print("PDF saved at:", file_path)

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

            print("Total pages extracted:", len(documents))

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            split_docs = splitter.split_documents(documents)
            print("Total chunks:", len(split_docs))

            vectorstore = FAISS.from_documents(split_docs, embeddings)

            vectorstore.save_local(FAISS_INDEX_PATH)
            print("FAISS index saved to disk.")

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
# ASK QUESTION (PHASE 3)
# ===============================

@csrf_exempt
def ask_question(request):
    global vectorstore
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
                return JsonResponse({"error": "No document uploaded yet."})

            # ===============================
            # PHASE 2 — RETRIEVAL
            # ===============================

            retrieved = vectorstore.similarity_search_with_score(query, k=7)

            threshold = 1.5
            filtered = [(doc, score) for doc, score in retrieved if score < threshold]

            if not filtered:
                filtered = retrieved[:3]

            documents = [doc for doc, score in filtered]
            scores = [float(score) for doc, score in filtered]

            context_parts = []

            for i, doc in enumerate(documents, start=1):
                 context_parts.append(f"[{i}] {doc.page_content}")
            
            context = "\n\n".join(context_parts)

            # ===============================
            # GENERATOR
            # ===============================

            prompt = f"""
You are a helpful assistant.

Use ONLY the provided evidence to answer the question.

Cite the evidence number in square brackets when using information.

Example:
RAG improves accuracy by retrieving documents [1].

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
                print("Gemini API Error:", response.text)
                return JsonResponse({"error": response.text}, status=500)

            result = response.json()

            answer_text = result["candidates"][0]["content"]["parts"][0]["text"]

            answer_embedding = embeddings.embed_query(answer_text)
            context_embedding = embeddings.embed_query(context)

            alignment_score = cosine_similarity(
            [answer_embedding],[context_embedding])[0][0]

            # ===============================
            # PHASE 3 — VERIFIER
            # ===============================

            verification_prompt = f"""
You are a fact verification system.

Evidence:
{context}

Generated Answer:
{answer_text}

Evaluate whether the answer is fully supported by the evidence.

Return ONLY JSON:

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

            for doc in documents:
                sources.append({
                    "document": doc.metadata["source"],
                    "page": doc.metadata["page"],
                    "chunk": doc.page_content,
                    "link": f"/media/{doc.metadata['source']}#page={doc.metadata['page']}"})

            # ===============================
            # FINAL RESPONSE
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