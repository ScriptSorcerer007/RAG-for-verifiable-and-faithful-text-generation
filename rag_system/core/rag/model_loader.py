from sentence_transformers import SentenceTransformer, CrossEncoder
import threading

_lock = threading.Lock()

embedding_model = None
reranker_model = None


def load_models():
    global embedding_model, reranker_model

    with _lock:
        if embedding_model is None:
            embedding_model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

        if reranker_model is None:
            reranker_model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2"
            )


load_models()