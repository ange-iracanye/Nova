import torch
import torch.nn as nn
import torch.optim as optim



class Trainer:

    def __init__(
        self,
        model,
        learning_rate=0.001
    ):

        self.model = model

        self.loss_function = nn.CrossEntropyLoss()


        self.optimizer = optim.Adam(
            model.parameters(),
            lr=learning_rate
        )



    def train_step(
        self,
        inputs,
        targets
    ):

        self.optimizer.zero_grad()


        predictions = self.model(
            inputs
        )


        predictions = predictions.view(
            -1,
            predictions.size(-1)
        )


        targets = targets.view(
            -1
        )


        loss = self.loss_function(
            predictions,
            targets
        )


        loss.backward()


        self.optimizer.step()


        return loss.item()