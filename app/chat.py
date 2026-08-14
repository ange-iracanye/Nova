import numpy as np

from save_model import load
from knowledge import Knowledge
from student_ai import process
from student_profile import get_profile
from personality import introduce, format_answer
from model_config import CONTEXT_LENGTH


print("Loading Nova...")


saved = load("nova_brain.pkl")

if saved is None:
    print("No trained brain found.")
    exit()


brain = saved["brain"]
tokenizer = saved["tokenizer"]

knowledge = Knowledge()


def generate(message):

    handled, response = process(message)

    if handled:
        return response

    if message.lower() == "profile":

        profile = get_profile()

        text = ""

        for key, value in profile.items():
            text += f"{key}: {value}\n"

        return text

    tokens = tokenizer.encode(message)

    if len(tokens) == 0:
        return "I don't know yet."

    while len(tokens) < CONTEXT_LENGTH:
        tokens.insert(0, 0)

    tokens = tokens[-CONTEXT_LENGTH:]

    answer = ""

    for _ in range(30):

        prediction = brain.predict(tokens)

        next_token = np.argmax(prediction)

        answer += tokenizer.decode([next_token]) + " "

        tokens.append(next_token)

        tokens = tokens[-CONTEXT_LENGTH:]

    return answer.strip()


print(introduce())
print("Nova is ready.")
print("Commands:")
print("profile")
print("exit")


while True:

    user = input("\nYou: ")

    if user.lower() == "exit":
        break

    answer = generate(user)

    print(format_answer(answer))