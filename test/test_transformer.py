import numpy as np

from transformer import TransformerBlock


block = TransformerBlock(
    8
)


inputs = np.random.randn(
    6,
    8
)


output = block.forward(
    inputs
)


print("Shape:")

print(
    output.shape
)

print()

print(output)