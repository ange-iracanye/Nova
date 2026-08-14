from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class EmbeddingSearch:

    def __init__(self):

        print("Loading embedding model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        self.texts = []

        self.embeddings = []

    def clear(self):

        self.texts.clear()

        self.embeddings.clear()

    def add(self, text):

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        self.texts.append(text)

        self.embeddings.append(embedding)

    def search(self, query, top_k=20):

        if not self.texts:

            return []

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        scores = cosine_similarity(
            [query_embedding],
            np.array(self.embeddings)
        )[0]

        ranked = sorted(

            zip(self.texts, scores),

            key=lambda x: x[1],

            reverse=True

        )

        return ranked[:top_k]