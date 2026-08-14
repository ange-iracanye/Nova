from ollama import chat


class LocalLLM:

    def __init__(self):

        print("Loading Qwen2.5...")

        self.model = "qwen2.5:1.5b"

        print("Qwen2.5 ready.")


    # =====================================
    # GENERATION SETTINGS
    # =====================================

    def get_temperature(self, creativity):

        temperatures = {

            "low": 0.2,

            "medium": 0.5,

            "high": 0.8
        }

        return temperatures.get(
            creativity,
            0.5
        )


    # =====================================
    # ANSWER
    # =====================================

    def answer(
        self,
        system,
        user,
        creativity="medium"
    ):

        temperature = (
            self.get_temperature(
                creativity
            )
        )


        response = chat(

            model=self.model,

            messages=[

                {
                    "role":
                        "system",

                    "content":
                        system
                },

                {
                    "role":
                        "user",

                    "content":
                        user
                }

            ],

            options={

                "temperature":
                    temperature,

                "top_p":
                    0.9,

                "repeat_penalty":
                    1.05
            }
        )


        return response[
            "message"
        ][
            "content"
        ]