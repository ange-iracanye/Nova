import os


KNOWLEDGE_FILE = "conversations/knowledge.txt"



class Knowledge:


    def __init__(self):

        folder = "conversations"

        if not os.path.exists(folder):

            os.makedirs(folder)



        if not os.path.exists(KNOWLEDGE_FILE):

            open(
                KNOWLEDGE_FILE,
                "w",
                encoding="utf-8"
            ).close()



    def save(self, fact):

        with open(
            KNOWLEDGE_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                fact + "\n"
            )



    def read(self):

        with open(
            KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()