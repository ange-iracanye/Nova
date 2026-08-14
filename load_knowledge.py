import os

from retrieval.embeddings import EmbeddingSearch

db = EmbeddingSearch()

folder = "data/knowledge"

for filename in os.listdir(folder):
    if filename.endswith(".txt"):
        path = os.path.join(folder, filename)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if line:
                    db.add(line)

print("Loaded", len(db.texts), "knowledge entries.")

os.makedirs("data", exist_ok=True)

db.model.save("data/model")