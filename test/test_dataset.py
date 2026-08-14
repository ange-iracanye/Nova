from dataset import TextDataset


class SimpleTokenizer:

    def encode(self, text):

        return [
            ord(character)
            for character in text
        ]



with open(
    "data.txt",
    "r",
    encoding="utf-8"
) as file:

    text = file.read()



dataset = TextDataset(
    text,
    SimpleTokenizer(),
    10
)


x, y = dataset[0]


print(x)

print(y)