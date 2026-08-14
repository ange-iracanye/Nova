import torch

from models.embedding import Embedding


model = Embedding(
    vocab_size=100,
    embedding_size=64
)


tokens = torch.tensor([
    [5, 2, 10, 8]
])


output = model(tokens)

print(output.shape)