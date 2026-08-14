import json
import os


HISTORY_FILE = "conversation.json"



def load_history():

    if not os.path.exists(HISTORY_FILE):

        return []


    with open(
        HISTORY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)





def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4
        )





def add_message(role, text):

    history = load_history()


    history.append(
        {
            "role": role,
            "text": text
        }
    )


    save_history(
        history
    )





def get_context(limit=10):

    history = load_history()


    recent = history[-limit:]


    context = ""


    for message in recent:

        context += (
            message["role"]
            + ": "
            + message["text"]
            + "\n"
        )


    return context





def clear_history():

    save_history([])