from .model_loader import reranker_model


class ReRanker:

    def __init__(self):
        self.model = reranker_model

    def rerank(self, query, documents, top_k=5):

        if not documents:
            return []

        pairs = [(query, doc.page_content) for doc in documents]

        scores = self.model.predict(
            pairs,
            batch_size=8,
            show_progress_bar=False
        )

        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked[:top_k]