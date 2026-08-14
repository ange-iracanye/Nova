from datetime import datetime


class Logger:

    def log(self, text):

        print(

            "[",

            datetime.now().strftime("%H:%M:%S"),

            "]",

            text

        )