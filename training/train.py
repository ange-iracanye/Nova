from dataset import Dataset
from tokenizer import Tokenizer
from brain import Brain
from save_model import save
from model_config import CONTEXT_LENGTH, EPOCHS


print("Loading data...")


data = Dataset(
    "data"
)


text = data.text


print(
    "Characters loaded:",
    len(text)
)


print("Building tokenizer...")


tokenizer = Tokenizer()

tokenizer.build(
    text
)


tokens = tokenizer.encode(
    text
)


vocabulary_size = len(
    tokenizer.words
)


print(
    "Vocabulary size:",
    vocabulary_size
)


print("Creating Nova brain...")


brain = Brain(
    vocabulary_size
)


print("Training...")


for epoch in range(EPOCHS):


    total_error = 0


    for i in range(
        len(tokens) - CONTEXT_LENGTH - 1
    ):


        context = tokens[
            i:i + CONTEXT_LENGTH
        ]


        target = tokens[
            i + CONTEXT_LENGTH
        ]


        loss = brain.learn(
            context,
            target,
            0.01
        )


        total_error += loss



    if epoch % 100 == 0:

        print(
            "Epoch:",
            epoch,
            "Loss:",
            total_error
        )



print("Saving Nova...")


save(
    {
        "brain": brain,
        "tokenizer": tokenizer
    },
    "nova_brain.pkl"
)


print("Nova learned.")