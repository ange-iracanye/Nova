from retrieval.embeddings import EmbeddingSearch


class KnowledgeSearch:

    def __init__(self):

        self.searcher = EmbeddingSearch()

    def search(self, question, top_k=20):

        results = self.searcher.search(

            question,

            top_k

        )

        if not results:

            return None

        keywords = {

            w.lower()

            for w in question.split()

            if len(w) > 2

        }

        rescored = []

        for text, similarity in results:

            lower = text.lower()

            keyword_bonus = sum(

                1

                for word in keywords

                if word in lower

            )

            final_score = similarity + keyword_bonus * 0.15

            rescored.append(

                (text, final_score)

            )

        rescored.sort(

            key=lambda x: x[1],

            reverse=True

        )

        unique = []

        seen = set()

        for text, score in rescored:

            if text in seen:

                continue

            seen.add(text)

            unique.append(text)

            if len(unique) == 3:

                break

        return unique