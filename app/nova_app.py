import tkinter as tk
import numpy as np

from save_model import load
from knowledge import Knowledge
from model_config import CONTEXT_LENGTH
from voice import listen, speak


print("Loading Nova...")


saved = load(
    "nova_brain.pkl"
)


if saved is None:

    print("Train Nova first.")

    exit()


brain = saved["brain"]

tokenizer = saved["tokenizer"]


knowledge = Knowledge()



def generate(message):


    facts = knowledge.read()


    for fact in facts.split("\n"):

        if fact != "" and fact.lower() in message.lower():

            return (
                "I remember: "
                + fact
            )



    tokens = tokenizer.encode(
        message
    )


    if len(tokens) == 0:

        return "I don't know yet."



    while len(tokens) < CONTEXT_LENGTH:

        tokens.insert(
            0,
            0
        )


    tokens = tokens[-CONTEXT_LENGTH:]


    result = ""


    for i in range(30):


        prediction = brain.predict(
            tokens
        )


        next_token = np.argmax(
            prediction
        )


        word = tokenizer.decode(
            [next_token]
        )


        result += word + " "


        tokens.append(
            next_token
        )


        tokens = tokens[-CONTEXT_LENGTH:]



    return result.strip()




def send():


    user = entry.get()


    if user == "":

        return



    chat.insert(
        tk.END,
        "You: "
        + user
        + "\n"
    )


    answer = generate(
        user
    )


    chat.insert(
        tk.END,
        "Nova: "
        + answer
        + "\n\n"
    )


    speak(
        answer
    )


    entry.delete(
        0,
        tk.END
    )



def voice_input():


    text = listen()


    if text != "":

        entry.delete(
            0,
            tk.END
        )


        entry.insert(
            0,
            text
        )


        send()




window = tk.Tk()

window.title(
    "Nova AI"
)


window.geometry(
    "600x500"
)



chat = tk.Text(
    window
)

chat.pack(
    padx=10,
    pady=10
)



entry = tk.Entry(
    window
)

entry.pack(
    fill="x",
    padx=10
)



send_button = tk.Button(
    window,
    text="Send",
    command=send
)

send_button.pack(
    pady=5
)



voice_button = tk.Button(
    window,
    text="🎤 Talk",
    command=voice_input
)

voice_button.pack(
    pady=5
)



window.mainloop()