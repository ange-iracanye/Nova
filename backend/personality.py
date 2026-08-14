import random

class Personality:

    greetings=[

        "Hello! Ready to learn?",

        "Hi! What are we studying today?",

        "Welcome back."

    ]

    bye=[

        "See you soon!",

        "Good luck studying!",

        "Have a great day!"

    ]

    thanks=[

        "You're welcome!",

        "Happy to help!",

        "Anytime!"

    ]

    def random(self,items):

        return random.choice(items)