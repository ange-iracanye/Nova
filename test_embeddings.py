from retrieval.embeddings import EmbeddingSearch

model = EmbeddingSearch()

sentences = [

    "Gravity pulls objects toward Earth.",

    "Photosynthesis allows plants to produce food.",

    "Napoleon became emperor of France."

]

vectors = model.encode(sentences)

question = model.encode([
    "Why do things fall?"
])[0]

scores = []

for i, vector in enumerate(vectors):

    score = model.similarity(
        question,
        vector
    )

    scores.append(
        (score, sentences[i])
    )

scores.sort(reverse=True)

print()

print("Best match:")

print(scores[0][1])

print("Similarity:", scores[0][0])