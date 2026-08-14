import os
import pickle


CHECKPOINT_FOLDER = "checkpoints"


if not os.path.exists(CHECKPOINT_FOLDER):
    os.makedirs(CHECKPOINT_FOLDER)


def save(model, filename="nova.pkl"):

    path = os.path.join(
        CHECKPOINT_FOLDER,
        filename
    )

    with open(path, "wb") as file:

        pickle.dump(model, file)


def load(filename="nova.pkl"):

    path = os.path.join(
        CHECKPOINT_FOLDER,
        filename
    )

    if not os.path.exists(path):

        return None


    with open(path, "rb") as file:

        return pickle.load(file)