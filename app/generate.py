import numpy as np

from dataset import Dataset
from tokenizer import Tokenizer
from model import LanguageModel
from trainer import Trainer
from save_model import save


data = Dataset("data/training.txt")


tokenizer = Tokenizer()

tokenizer.build(data.text)


tokens = tokenizer.encode(data.text)


context_size = 20


model = LanguageModel(
    len(tokenizer.characters),
    context_size
)


trainer = Trainer(model)


for epoch in range(500):

    for i in range(len(tokens) - context_size - 1):

        context = np.array(
            tokens[i:i + context_size]
        )

        target = tokens[i + context_size]


        trainer.train_step(
            context,
            target
        )


def generate(start, length):

    result = start


    context = tokenizer.encode(start)


    context = context[-context_size:]


    while len(context) < context_size:

        context.insert(0, 0)


    for i in range(length):

        probabilities = model.predict(
            np.array(context)
        )


        next_token = np.argmax(probabilities)


        character = tokenizer.decode(
            [next_token]
        )


        result += character


        context.append(next_token)

        context = context[-context_size:]


    return result



save(model, "nova_brain.pkl")


print("Nova:")

print(
    generate("hello", 50)
)