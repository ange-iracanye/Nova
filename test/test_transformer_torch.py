import torch

from models.transformer import TransformerBlock


block = TransformerBlock(
    embedding_size=64,
    heads=8
)


x = torch.randn(
    1,
    10,
    64
)


output = block(
    x
)


print(output.shape)