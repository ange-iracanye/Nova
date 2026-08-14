import json
import os


FILE = "settings.json"



def load_settings():

    print("Looking for:", os.path.abspath(FILE))


    with open(
        FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()


    print("File contains:")
    print(content)


    return json.loads(content)



def get_name():

    settings = load_settings()

    return settings["name"]



def get_personality():

    settings = load_settings()

    return settings["personality"]