import json


class Tokenizer:

    def __init__(self):

        self.words = []
        self.word_to_id = {}
        self.id_to_word = {}



    def build(self, text):

        words = text.lower().split()


        self.words = sorted(
            list(set(words))
        )


        self.word_to_id = {
            word: i
            for i, word in enumerate(self.words)
        }


        self.id_to_word = {
            i: word
            for word, i in self.word_to_id.items()
        }



    def encode(self, text):

        words = text.lower().split()


        return [
            self.word_to_id[word]
            for word in words
            if word in self.word_to_id
        ]



    def decode(self, tokens):

        return " ".join(
            self.id_to_word[token]
            for token in tokens
        )



    def save(self, path):

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                {
                    "words": self.words
                },
                file
            )



    def load(self, path):

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)


        self.words = data["words"]


        self.word_to_id = {
            word: i
            for i, word in enumerate(self.words)
        }


        self.id_to_word = {
            i: word
            for word, i in self.word_to_id.items()
        }