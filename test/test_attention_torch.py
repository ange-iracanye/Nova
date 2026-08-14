import torch

from models.attention import MultiHeadAttention



attention = MultiHeadAttention(
    embedding_size=64,
    heads=8
)


x = torch.randn(
    1,
    10,
    64
)


output = attention(x)


print(output.shape)