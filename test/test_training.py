import torch

from models.nova_model import NovaModel
from trainer import Trainer



model = NovaModel(
    vocab_size=100,
    embedding_size=64,
    heads=8,
    layers=2,
    max_tokens=128
)


trainer = Trainer(
    model
)



inputs = torch.tensor(
    [
        [1,2,3,4]
    ]
)


targets = torch.tensor(
    [
        [2,3,4,5]
    ]
)



loss = trainer.train_step(
    inputs,
    targets
)


print(
    "Loss:",
    loss
)