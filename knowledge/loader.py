import os

from retrieval.search import KnowledgeSearch


class KnowledgeLoader:

    def __init__(self):
        self.search = KnowledgeSearch()

    def load(self, folder="data/knowledge"):

        self.search.searcher.clear()

        total = 0

        for filename in os.listdir(folder):

            if not filename.endswith(".txt"):
                continue

            path = os.path.join(folder, filename)

            with open(path, "r", encoding="utf-8") as file:

                for line in file:

                    line = line.strip()

                    if not line:
                        continue

                    self.search.searcher.add(line)
                    total += 1

        print(f"Loaded {total} facts.")

        return self.search