class HybridRetriever:

    def __init__(self, dense_retriever, bm25_retriever):
        self.dense = dense_retriever
        self.bm25 = bm25_retriever

    def normalize(self, scores):
        min_s = min(scores)
        max_s = max(scores)
        return [(s - min_s) / (max_s - min_s + 1e-8) for s in scores]

    def retrieve(self, query, k=10):

        # =========================
        # 1. Dense Retrieval
        # =========================
        dense_results = self.dense.similarity_search_with_score(query, k=k)

        dense_docs = [doc for doc, score in dense_results]
        dense_scores = [score for doc, score in dense_results]

        # FAISS gives distance → convert to similarity
        dense_scores = [-s for s in dense_scores]

        # =========================
        # 2. BM25 Retrieval
        # =========================
        bm25_results = self.bm25.retrieve(query, k=k)

        bm25_docs = [doc for doc, score in bm25_results]
        bm25_scores = [score for doc, score in bm25_results]

        # =========================
        # 3. Normalize Scores
        # =========================
        dense_scores = self.normalize(dense_scores)
        bm25_scores = self.normalize(bm25_scores)

        # =========================
        # 4. Merge (Score Fusion)
        # =========================
        score_dict = {}

        # Dense contribution
        for doc, score in zip(dense_docs, dense_scores):
            score_dict[doc.page_content] = {
                "doc": doc,
                "score": 0.5 * score
            }

        # BM25 contribution
        for doc, score in zip(bm25_docs, bm25_scores):
            if doc.page_content in score_dict:
                score_dict[doc.page_content]["score"] += 0.5 * score
            else:
                score_dict[doc.page_content] = {
                    "doc": doc,
                    "score": 0.5 * score
                }

        # =========================
        # 5. Sort Final Results
        # =========================
        ranked = sorted(
            score_dict.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return [(item["doc"], item["score"]) for item in ranked[:k]]