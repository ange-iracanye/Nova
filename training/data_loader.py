import os


class DataLoader:


    def __init__(self, folder):

        self.folder = folder



    def load_text(self):

        text = ""


        for filename in os.listdir(self.folder):

            if filename.endswith(".txt"):

                path = os.path.join(
                    self.folder,
                    filename
                )


                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    text += file.read()

                    text += "\n"



        return text