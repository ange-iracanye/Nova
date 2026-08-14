from dataset import Dataset
from tokenizer import Tokenizer


data = Dataset("data/training.txt")


text = data.text


tokenizer = Tokenizer()

tokenizer.build(text)


numbers = tokenizer.encode(text)


print("Original text:")
print(text)


print("\nConverted into numbers:")
print(numbers)


print("\nBack into text:")
print(tokenizer.decode(numbers))