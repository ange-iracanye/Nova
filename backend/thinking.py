class Thinking:

    FOLLOW_UP = [

        "why",

        "how",

        "tell me more",

        "again",

        "another",

        "example",

        "summarize",

        "shorter",

        "simpler",

        "explain"

    ]

    def is_follow_up(

        self,

        message

    ):

        m = message.lower()

        for word in self.FOLLOW_UP:

            if word in m:

                return True

        return False