from dataset import Dataset
from tokenizer import Tokenizer
from model import LanguageModel
from trainer import Trainer


data = Dataset("data/training.txt")


tokenizer = Tokenizer()

tokenizer.build(data.text)


tokens = tokenizer.encode(data.text)


model = LanguageModel(len(tokenizer.characters))


trainer = Trainer(model)


for epoch in range(100):

    total_loss = 0


    for i in range(len(tokens)-1):

        current = tokens[i]

        next_token = tokens[i+1]


        loss = trainer.train_step(
            current,
            next_token
        )


        total_loss += loss


    if epoch % 10 == 0:
        print(
            "Epoch:",
            epoch,
            "Loss:",
            total_loss
        )


print("Training finished")