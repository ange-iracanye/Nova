from model import LanguageModel
from tokenizer import Tokenizer
from dataset import Dataset


data = Dataset("data/training.txt")


tokenizer = Tokenizer()

tokenizer.build(data.text)


vocab_size = len(tokenizer.characters)


model = LanguageModel(vocab_size)


token = tokenizer.encode("h")[0]


prediction = model.predict(token)


print("Prediction probabilities:")
print(prediction)