from rank_bm25 import BM25Okapi

class BM25Retriever:

    def __init__(self, documents):

        self.documents = documents

        tokenized = [doc.page_content.split() for doc in documents]

        self.bm25 = BM25Okapi(tokenized)


    def retrieve(self, query, k=10):

        tokenized_query = query.split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [(doc, score) for doc, score in ranked[:k]]