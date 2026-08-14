import numpy as np

from layer_norm import LayerNorm


layer = LayerNorm(4)

x = np.array([
    5.0,
    10.0,
    15.0,
    20.0
])

print(layer.forward(x))