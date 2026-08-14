import torch

from models.nova_model import NovaModel



model = NovaModel(
    vocab_size=100,
    embedding_size=64,
    heads=8,
    layers=2,
    max_tokens=128
)


tokens = torch.tensor(
    [
        [5, 20, 7, 9]
    ]
)


output = model(
    tokens
)


print(output.shape)