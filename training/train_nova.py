import os
import torch

from torch.utils.data import DataLoader

from models.nova_model import NovaModel
from trainer import Trainer
from dataset import TextDataset
from tokenizer import Tokenizer



def load_data(folder):

    text = ""


    for file in os.listdir(folder):

        if file.endswith(".txt"):

            path = os.path.join(
                folder,
                file
            )


            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                text += f.read()
                text += "\n"


    return text




print("Loading data...")


text = load_data(
    "data"
)


print(
    "Characters loaded:",
    len(text)
)



print("Building tokenizer...")


tokenizer = Tokenizer()

tokenizer.build(
    text
)


vocab_size = len(
    tokenizer.words
)


print(
    "Vocabulary size:",
    vocab_size
)



tokenizer.save(
    "tokenizer.json"
)




dataset = TextDataset(
    text,
    tokenizer,
    sequence_length=16
)



loader = DataLoader(
    dataset,
    batch_size=4,
    shuffle=True
)



print("Creating Nova brain...")



model = NovaModel(
    vocab_size=vocab_size,
    embedding_size=64,
    heads=8,
    layers=2,
    max_tokens=64
)



trainer = Trainer(
    model,
    learning_rate=0.001
)



print("Training...")



epochs = 100



for epoch in range(epochs):

    total_loss = 0


    for inputs, targets in loader:

        loss = trainer.train_step(
            inputs,
            targets
        )


        total_loss += loss



    print(
        "Epoch",
        epoch + 1,
        "Loss:",
        total_loss
    )




torch.save(
    model.state_dict(),
    "nova_model.pt"
)



print("Nova saved.")