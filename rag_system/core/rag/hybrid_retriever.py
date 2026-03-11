class HybridRetriever:

    def __init__(self, dense_retriever, bm25_retriever):

        self.dense = dense_retriever
        self.bm25 = bm25_retriever


    def retrieve(self, query, k=10):

        dense_results = self.dense.similarity_search(query, k=k)

        bm25_results = self.bm25.retrieve(query, k=k)

        combined = dense_results + bm25_results

        unique = {}

        for doc in combined:
            unique[doc.page_content] = doc

        return list(unique.values())[:k]