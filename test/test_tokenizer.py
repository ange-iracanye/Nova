from tokenizer import Tokenizer


text = "hello my ai"


tokenizer = Tokenizer()

tokenizer.build(text)


encoded = tokenizer.encode("hello")

print("Numbers:")
print(encoded)


decoded = tokenizer.decode(encoded)

print("Text:")
print(decoded)