import torch

from models.nova_model import NovaModel
from tokenizer import Tokenizer

from memory import remember, get_memory
from study import explain, quiz
from retrieval import find_information
from conversation import add_message, get_context



# Load tokenizer

tokenizer = Tokenizer()

tokenizer.load(
    "tokenizer.json"
)



# Load Nova model

model = NovaModel(
    vocab_size=len(tokenizer.words),
    embedding_size=64,
    heads=8,
    layers=2,
    max_tokens=64
)



model.load_state_dict(
    torch.load(
        "nova_model.pt"
    )
)


model.eval()





def handle_memory(user):

    text = user.lower()


    if "my name is" in text:

        name = user.lower().split(
            "my name is"
        )[-1].strip()


        remember(
            "name",
            name
        )


        return "I will remember your name."



    if "what is my name" in text:

        memory = get_memory()


        if "name" in memory:

            return (
                "Your name is "
                + memory["name"]
            )


        return "I don't know your name yet."



    return None






def handle_study(user):

    text = user.lower()


    if text.startswith(
        "explain "
    ):

        subject = text.replace(
            "explain ",
            ""
        )


        document_answer = find_information(
            subject
        )


        if document_answer:

            return document_answer



        return explain(
            subject
        )



    if text.startswith(
        "quiz me on "
    ):

        subject = text.replace(
            "quiz me on ",
            ""
        )


        return quiz(
            subject
        )



    return None






def generate(prompt):

    tokens = tokenizer.encode(
        prompt
    )


    if len(tokens) == 0:

        tokens = [0]



    tokens = torch.tensor(
        [
            tokens
        ],
        dtype=torch.long
    )



    for _ in range(30):

        output = model(
            tokens[:, -64:]
        )


        probabilities = torch.softmax(
            output[0, -1],
            dim=0
        )


        next_token = torch.multinomial(
            probabilities,
            1
        )


        tokens = torch.cat(
            [
                tokens,
                next_token.reshape(1, 1)
            ],
            dim=1
        )



    return tokenizer.decode(
        tokens[0].tolist()
    )







print(
    "Nova student assistant ready."
)


print(
    "Commands:"
)

print(
    "memory"
)

print(
    "exit"
)






while True:

    user = input(
        "\nYou: "
    )


    if user.lower() == "exit":

        break



    add_message(
        "User",
        user
    )



    answer = handle_memory(
        user
    )



    if answer is None:

        answer = handle_study(
            user
        )



    if answer is None:

        context = get_context()

        answer = generate(
            context
        )



    add_message(
        "Nova",
        answer
    )



    print(
        "\nNova:",
        answer
    )