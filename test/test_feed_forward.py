import torch

from models.feed_forward import FeedForward
from models.layer_norm import LayerNorm



x = torch.randn(
    1,
    10,
    64
)



ff = FeedForward(
    64
)


norm = LayerNorm(
    64
)



output = ff(x)

output = norm(output)



print(output.shape)